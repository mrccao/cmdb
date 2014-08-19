import re
import sys
import inspect

from flask import render_template, redirect, url_for, abort, flash, request, current_app, make_response, jsonify
from flask.views import View
from flask.ext.login import login_required, current_user
from flask.ext.sqlalchemy import get_debug_queries
from flask_sqlalchemy import Model as SqlAlchemyModel
from . import main
from .forms import L2DomainForm, L3DomainForm, SystemForm, VendorForm, HardwareModelForm, HardwareForm, SystemCategoryForm, CountryForm, CountyForm, HardwareTypeForm, SoftwareForm, SoftwareVersionForm, CityForm, StreetForm, LocationForm, SearchForm
from .. import db
from ..models import L2Domain, L3Domain, System, Vendor, HardwareModel, Hardware, SystemCategory, County, Country, HardwareType, Software, SoftwareVersion, City, Street, Location
from .. import models
from . import forms
from wtforms.widgets import Select
from jinja2.exceptions import TemplateNotFound
import sqlalchemy
from whoosh.qparser import MultifieldParser
from whoosh.collectors import UnlimitedCollector

import whoosh.fields

from ..navbar_group import navbar

def pretty_print(text):
    text = re.sub("([a-z])([A-Z])","\g<1> \g<2>", text)
    return text.replace("_", " ")
    
@main.route('/instant-search', methods=['POST'])
@login_required
def instant_search():
    results = list()
    search_term_original = request.form["search"]
    search_term_original = search_term_original.strip().strip("*")
    search_term = "*%s*" % search_term_original
    for model in get_model_classes():
        fields = list()
        for field in model()._get_indexable_columns():
            if field != "id":
                fields.append(field)
        mparser = MultifieldParser(fields, schema=model()._get_schema())
        query = mparser.parse(search_term)
        with model()._get_index().searcher() as searcher:
            for h in searcher.search(query, terms=True):
                model_id, model_type, ci_name, score = h["model_id"], h["model_name"], h["name"], h.score
                matched_terms = list()
                for field, text in h.matched_terms():
                    field = "<code>%s</code>" % pretty_print(field)
                    text = ("<mark class='bg-danger'>%s</mark>" % search_term_original).join(text.split(search_term_original))
                    matched_terms.append(": ".join([field, text]))
                model_name = pretty_print(model_type)
                results.append((score, model_id, model_name, model_type, ci_name, matched_terms))
    results = sorted(results, key=lambda attr: attr[0], reverse=True)
    html_results = ""
    for score, model_id, model_name, model_type, ci_name, matched_terms in results:
        html_results += "<tr>"
        html_results += '<td><a href="/edit/%s/%s">%s</a></td>' % (model_type.lower(), model_id, model_name)
        html_results += '<td><a href="/edit/%s/%s">%s</a></td>' % (model_type.lower(), model_id, ci_name)
        html_results += '<td><a href="/edit/%s/%s">' % (model_type.lower(), model_id)
        for matched_term in matched_terms:
            html_results += "<p>" + matched_term + "</p>"
        html_results += "</a></td></tr>"
    return html_results


"""
@main.route('/search', methods=['GET', 'POST'])
@login_required
def search():
    search_form = SearchForm()
    results = list()
    if request.method == "POST":
        search_term_original = request.form["search"]
        search_term_original = search_term_original.strip().strip("*")
        search_term = "*%s*" % search_term_original
        for model in get_model_classes():
            fields = list()
            for field in model()._get_indexable_columns():
                if field != "id":
                    fields.append(field)
            mparser = MultifieldParser(fields, schema=model()._get_schema())
            query = mparser.parse(search_term)
            with model()._get_index().searcher() as searcher:
                for h in searcher.search(query, terms=True):
                    model_id, model_type, ci_name, score = h["model_id"], h["model_name"], h["name"], h.score
                    matched_terms = list()
                    for field, text in h.matched_terms():
                        field = "<code>%s</code>" % pretty_print(field)
                        text = ("<mark class='bg-danger'>%s</mark>" % search_term_original).join(text.split(search_term_original))
                        matched_terms.append(": ".join([field, text]))
                    model_name = pretty_print(model_type)
                    results.append((score, model_id, model_name, model_type, ci_name, matched_terms))
        results = sorted(results, key=lambda attr: attr[0], reverse=True)
        return render_template('search.html', results=results, navbar_groups=navbar, search_form=search_form)
    return render_template('search.html', results=[], navbar_groups=navbar, search_form=search_form)
"""


@main.route('/', methods=['GET'])
@login_required
def index():
    search_form = SearchForm()
    return render_template('index.html', navbar_groups=navbar, search_form=search_form)

def get_model_from_string(model_string):
    model_string = model_string.replace("_", "")
    for name, cls in inspect.getmembers(sys.modules["app.models"]):
        name = name.lower()
        if name == model_string:
            return cls
 
@main.route('/dependencies/<model>/<int:id>', methods=['GET', 'POST'])
@login_required
def dependencies(model, id):
    model = get_model_from_string(model)
    model_instance = model.query.filter_by(id=id).first()
    dependencies = list()
    for dependency in model_instance.get_dependencies():
        model_friendly_name = dependency.get_model_friendly_name()
        model = type(dependency).__name__.lower()
        name = dependency.name
        id = dependency.id
        dependencies.append((id, name, model, model_friendly_name))
    return jsonify(results=dependencies)


@main.route('/parent_child/<parent>/<child>/<parent_id>', methods=['GET', 'POST'])
@login_required
def parent_child(parent, child, parent_id):
    args = [parent, child, parent_id]
    options = list()
    if "undefined" in args or "null" in args:
        options.append(("null", "null", "None"))
        return jsonify(options=options)

    parent_cls = get_model_from_string(parent)
    child_cls = get_model_from_string(child)
    for row in child_cls.query.filter(getattr(child_cls, parent).has(id=parent_id)):
        #options += "<option parent='%s' value='%s'>%s</option>" % (parent_id, row.id, row.name)
        options.append((parent_id, row.id, row.name))
    if not options:
        options.append(("null", "null", "None"))
        #options = "<option parent='None' value='None'>None</option>"
    return jsonify(options=options)


def populate_one_to_many_choices(form, model):
    # Fill in the form choices from the models
    model_instance = model
    model_type = type(model)
    for column in model_instance.get_one_to_many_columns():
        if not hasattr(form, column):
            continue
        related_model = getattr(model_type, column).property.mapper.primary_base_mapper.entity
        choices = [(r_column.id, getattr(r_column, related_model.order_by)) for r_column in related_model.query.order_by(related_model.order_by)]
        if choices is None:
            choices = list()
        setattr(getattr(form, column), "choices", choices)
    return form



class EditorView(View):
    methods = ['GET', 'POST']

    def __init__(self, form, model):
        self.model = model
        self.form = form

    @staticmethod
    def update_row(form, model, add=False):
        changed = False
        foreign_keys = model.get_foreign_keys()
        one_to_many_keys = model.get_one_to_many_columns()
        for field in model.get_columns():
            if field in form.__dict__:
                if field in one_to_many_keys:
                    related_model = getattr(type(model), field).property.mapper.primary_base_mapper.entity
                    if type(getattr(form, field).data) is list:
                        data = related_model.query.filter(related_model.id.in_(getattr(form, field).data))
                    else:
                        data = related_model.query.filter_by(id=getattr(form, field).data)
                    try:
                        setattr(model, field, data.all())
                    except AttributeError:
                        setattr(model, field, data.first())
                elif field not in one_to_many_keys:
                    setattr(model, field, getattr(form, field).data)
        if add:
            model.id = None
        db.session.add(model)
        db.session.commit()
        model.update_index()
        return True


class AddView(EditorView):

    @login_required
    def dispatch_request(self):
        cascade = []
        if hasattr(self.model, "cascade"):
            cascade = self.model.cascade
        return AddView.generic_add(self.form(), self.model, cascade=cascade)

    @staticmethod
    def generic_add(form, model, cascade=None):
        search_form = SearchForm()
        model_type = model
        model_instance = model()
        form = populate_one_to_many_choices(form, model_instance)
        if form.validate_on_submit():
            AddView.update_row(form, model_instance, add=True)
            redirect_url = "/view/%s" % model_type.__name__.lower()
            return redirect(redirect_url)
        if cascade == None:
            cascade = list()
        template_name = 'edit_%s.html' % model_type.__name__.lower()
        for template in [template_name, "edit_model.html"]:
            try:
                return render_template(template, navbar_groups=navbar, model=model_instance, form=form, Table=model_instance, cascade=cascade, search_form=search_form)
            except TemplateNotFound:
                pass


class EditView(EditorView):

    @login_required
    def dispatch_request(self, id):
        cascade = []
        if hasattr(self.model, "cascade"):
            cascade = self.model.cascade
        return EditView.generic_edit(id, self.form(), self.model, cascade=cascade)

    @staticmethod
    def generic_edit(id, form, model, cascade=None):
        search_form = SearchForm()
        model_type = model
        model_instance = model.query.filter_by(id=id).first()
        form = populate_one_to_many_choices(form, model_instance)
        if form.validate_on_submit():
            redirect_url = "/view/%s" % model_type.__name__.lower()
            EditView.update_row(form, model_instance)
            return redirect(redirect_url)
        else:
            # Populate the form
            for field in model_instance.get_columns():
                if field in form.__dict__:
                    form_field = getattr(form, field)
                    if field in model_instance.get_one_to_many_columns():
                        #  Multi Select
                        data = getattr(model_instance, field)
                        if hasattr(data, "__class__") and "InstrumentedList" in data.__class__.__name__:
                            form_field.data = map(lambda x: x.id, data)
                        #  Single Select
                        else:
                            if hasattr(data, "first"):
                                data = data.first()
                                if data is not None:
                                    form_field.data = data.id
                                else:
                                    form_field.data = data
                            else:
                                form_field.data = data.id
                    else:
                        form_field.data = getattr(model_instance, field)
        if cascade is None:
            cascade = list()
        template_name = 'edit_%s.html' % model_type.__name__.lower()
        for template in [template_name, "edit_model.html"]:
            try:
                return render_template(template, navbar_groups=navbar, model=model_instance, form=form, Table=model_instance, cascade=cascade, search_form=search_form)
            except TemplateNotFound:
                pass

class DeleteView(View):
    methods = ['GET', 'POST']

    def __init__(self, model):
        self.model = model

    @login_required
    def dispatch_request(self, id):
        model_instance = self.model.query.filter_by(id=id).first()
        name = self.model.__name__.lower()
        redirect_url = ".view_%s" % name
        model_instance.delete_index()
        db.session.delete(model_instance)
        return redirect("/view/%s/" % name)

class ListView(View):
    methods = ['GET', 'POST']

    def __init__(self, model):
        self.model = model
        self.model_instance = model()
        self.table_view = self._table_view(self.model_instance, model.display_fields)
        self.table_view.records = model.query.order_by(self.table_view.order.by).all()
        if not self.table_view.order.asc:
            self.table_view.records.reverse()

    @login_required
    def dispatch_request(self):
        return ListView.generic_list(self.model(), self.table_view.displayed)

    @staticmethod
    def generic_list(model, displayed_fields=None):
        search_form = SearchForm()
        model_type = type(model)
        model_instance = model
        class table_view:
            name = type(model).__name__
            friendly_name = model.get_model_friendly_name()
            displayed = displayed_fields
            if not displayed_fields:
                displayed = list()
                for field in model.get_columns:
                    if field != "id":
                        displayed.append(field)
            class order:
                by = "id"
                if "name" in model.get_columns():
                    by = "name"
                _sort = request.args.get("sort")
                if _sort:
                    by = model.__dict__[_sort]
                _asc = request.args.get("asc") or 1
                asc = int(_asc)
        table_view.records = model.query.order_by(table_view.order.by).all()
        if not table_view.order.asc:
            table_view.records.reverse()
        return render_template('view_model.html',  navbar_groups=navbar, model=model_instance, Table=table_view, search_form=search_form)
    
    class _table_view(object):
        def __init__(self, model, displayed_fields=None):
            self.friendly_name = model.get_model_friendly_name()
            self.order = self._order(model)
            self.model = type(model)
            self.name = type(model).__name__
            self.displayed = displayed_fields

            if not self.displayed:
                self.displayed = list()
                for field in dir(model):
                    if getattr(model, field).__class__.__name__ == "InstrumentedAttribute":
                        if field != "id":
                            self.displayed.append(field)
        class _order:
            def __init__(self, model):
                self.by = "id"
                self.model = model
                if hasattr(self.model, "name"):
                    self.by = "name"
                _sort = request.args.get("sort")
                _asc = request.args.get("asc") or 1
                self.asc = int(_asc)
  

def get_form_classes():
    form_cls = list()
    for name, cls in inspect.getmembers(sys.modules["app.main.forms"]):
        if hasattr(cls, "__bases__"):
            base_cls = [str(base_cls.__bases__) for base_cls in cls.__bases__]
        for base_cl in base_cls:
            if "wtforms.ext.csrf.form.SecureForm" in base_cl and name.lower().endswith("form"):
                form_cls.append(cls)
    return form_cls
 
def get_model_classes():
    model_cls = set()
    for name, cls in inspect.getmembers(sys.modules["app.models"]):
        if inspect.isclass(cls) and issubclass(cls, SqlAlchemyModel):
            if cls.__name__.lower() not in ["user"]:
                model_cls.add(cls)
    return model_cls

def get_model_form_classes():
    model_forms = list()
    for model in get_model_classes():
        for form in get_form_classes():
            if "%sform" % model.__name__.lower() == form.__name__.lower():
                model_forms.append((model, form))
    return model_forms
            
for model, form in get_model_form_classes():
    name = model.__name__.lower()
    main.add_url_rule('/view/%s/' % name, view_func=ListView.as_view("view_%s" % name, model))
    main.add_url_rule('/add/%s/' % name, view_func=AddView.as_view("add_%s" % name, form, model))
    main.add_url_rule('/edit/%s/<int:id>' % name, view_func=EditView.as_view("edit_%s" % name, form, model))
    main.add_url_rule('/delete/%s/<int:id>' % name, view_func=DeleteView.as_view("delete_%s" % name, model))
