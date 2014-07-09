import sys
import json
import inspect

from flask import render_template, redirect, url_for, abort, flash, request,current_app, make_response, jsonify
from flask.views import View
from flask.ext.login import login_required, current_user
from flask.ext.sqlalchemy import get_debug_queries
from . import main
from .forms import L2DomainForm, L3DomainForm, SystemForm, VendorForm, HardwareModelForm, HardwareForm, SystemCategoryForm, CountryForm, CountyForm, HardwareTypeForm, SoftwareForm, SoftwareVersionForm, CityForm, StreetForm, LocationForm, SearchForm
from .. import db
from ..models import L2Domain, L3Domain, System, Vendor, HardwareModel, Hardware, SystemCategory, County, Country, HardwareType, Software, SoftwareVersion, City, Street, Location
from .. import models
from . import forms
from wtforms.widgets import Select
from jinja2.exceptions import TemplateNotFound

@main.route('/search', methods=['GET', 'POST'])
@login_required
def search():
    search_form = SearchForm()
    results = list()
    if request.method == "POST":
        search_term = request.form["search"]
        print search_term
        search_models = [System, Location, Hardware, HardwareModel, SoftwareVersion]
        for model in search_models:
            search_results = model.query.whoosh_search(search_term)
            for search_result in search_results:
                results.append(search_result)
    return render_template('search.html', results=results, search_form=search_form)


@main.route('/', methods=['GET'])
@login_required
def index():
    search_form = SearchForm()
    groups = [(Vendor, L2Domain, L3Domain)]
    return render_template('index.html', groups=groups, search_form=search_form)

@main.route('/system', methods=['GET'])
@login_required
def system():
    search_form = SearchForm()
    groups = [(System, SystemCategory)]
    return render_template('index.html', groups=groups, search_form=search_form)

@main.route('/hardware', methods=['GET'])
@login_required
def hardware():
    search_form = SearchForm()
    groups = [(Hardware, HardwareModel, HardwareType)]
    return render_template('index.html', groups=groups, search_form=search_form)

@main.route('/software', methods=['GET'])
@login_required
def software():
    search_form = SearchForm()
    groups = [(Software, SoftwareVersion)]
    return render_template('index.html', groups=groups, search_form=search_form)

@main.route('/locations', methods=['GET'])
@login_required
def locations():
    search_form = SearchForm()
    groups = [(Country, County, City, Street, Location)]
    return render_template('index.html', groups=groups, search_form=search_form)


@main.route('/parent_child/<parent>/<child>/<int:parent_id>', methods=['GET', 'POST'])
@login_required
def parent_child(parent, child, parent_id):
    parent = parent.replace("_", "")
    child = child.replace("_", "")
    parent_cls = None
    child_cls = None
    for name, cls in inspect.getmembers(sys.modules["app.models"]):
        name = name.lower()
        if name == parent:
            parent_cls = cls
        elif name == child:
            child_cls = cls
        if parent_cls and child_cls:
            break
    options = ""
    for row in child_cls.query.filter(getattr(child_cls, parent).has(id=parent_id)):
        options += "<option parent='%s' value='%s'>%s</option>" % (parent_id, row.id, row.name)
    return options


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
    return True


def generic_add(form, model, cascade=None):
    search_form = SearchForm()
    model_type = model
    model_instance = model()
    #if request.method == 'POST':
        #raise Exception()
    form = populate_one_to_many_choices(form, model_instance)
    if form.validate_on_submit():
        update_row(form, model_instance, add=True)
        redirect_url = "/view/%s" % model_type.__name__.lower()
        return redirect(redirect_url)
    if cascade == None:
        cascade = list()
    template_name = 'edit_%s.html' % model_type.__name__.lower()
    try:
        return render_template(template_name, form=form, Table=model_instance, cascade=cascade, search_form=search_form)
    except TemplateNotFound:
        return render_template('edit_model.html', form=form, Table=model_instance, cascade=cascade, search_form=search_form)

def generic_edit(id, form, model, cascade=None):
    search_form = SearchForm()
    model_type = model
    model_instance = model.query.filter_by(id=id).first()
    form = populate_one_to_many_choices(form, model_instance)
    if form.validate_on_submit():
        redirect_url = "/view/%s" % model_type.__name__.lower()
        update_row(form, model_instance)
        return redirect(redirect_url)
    else:
        # Populate the form
        for field in model_instance.get_columns():
            if field in form.__dict__:
                form_field = getattr(form, field)
                if field in model_instance.get_one_to_many_columns():
                    #  Multi Select
                    #elif hasattr(value, "__class__") and "InstrumentedList" in value.__class__.__name__:
                    #if form_field.widget.__class__ is Select and form_field.widget.multiple:
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
    try:
        return render_template(template_name, form=form, Table=model_instance, cascade=cascade, search_form=search_form)
    except TemplateNotFound:
        return render_template('edit_model.html', form=form, Table=model_type, cascade=cascade, search_form=search_form)

def generic_delete(id, model):
    row = model.query.filter_by(id=id).first()
    redirect_url = ".view_%s" % type(model).__name__.lower()
    db.session.delete(row)
    return redirect(url_for(redirect_url))

def generic_view(model, displayed_fields=None):
    search_form = SearchForm()
    class table_view:
        name = type(model).__name__
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
    return render_template('view_model.html', Table=table_view, search_form=search_form)


class AddView(View):
    methods = ['GET', 'POST']

    def __init__(self, form, model):
        self.model = model
        self.form = form

    @login_required
    def dispatch_request(self):
        cascade = []
        if hasattr(self.model, "cascade"):
            cascade = self.model.cascade
        return generic_add(self.form(), self.model, cascade=cascade)

class EditView(View):
    methods = ['GET', 'POST']

    def __init__(self, model, form):
        self.model = model
        self.form = form

    @login_required
    def dispatch_request(self, id):
        cascade = []
        if hasattr(self.model, "cascade"):
            cascade = self.model.cascade
        return generic_edit(id, self.form(), self.model, cascade=cascade)

class DeleteView(View):
    methods = ['GET', 'POST']

    def __init__(self, model):
        self.model = model

    @login_required
    def dispatch_request(self, id):
        row = self.model.query.filter_by(id=id).first()
        name = self.model.__name__.lower()
        redirect_url = ".view_%s" % name
        db.session.delete(row)
        return redirect("/view/%s/" % name)

class ListView(View):
    methods = ['GET', 'POST']

    def __init__(self, model):
        self.model = model
        self.table_view = self._table_view(model, model.display_fields)
        self.table_view.records = model.query.order_by(self.table_view.order.by).all()
        if not self.table_view.order.asc:
            self.table_view.records.reverse()

    @login_required
    def dispatch_request(self):
        return generic_view(self.model(), self.table_view.displayed)

    class _table_view(object):
        def __init__(self, model, displayed_fields=None):

            self.order = self._order(model)
            self.model = model
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
  

form_cls = list()
for name, cls in inspect.getmembers(sys.modules["app.main.forms"]):
    if hasattr(cls, "__bases__"):
        base_cls = [str(base_cls.__bases__) for base_cls in cls.__bases__]
    for base_cl in base_cls:
        if "wtforms.ext.csrf.form.SecureForm" in base_cl and name.lower().endswith("form"):
            form_cls.append(cls)
 
model_cls = list()
for name, cls in inspect.getmembers(sys.modules["app.models"]):
    base_cls = list()
    if hasattr(cls, "__bases__"):
        base_cls = [str(base_cls.__bases__) for base_cls in cls.__bases__]
    for base_cl in base_cls:
        if "flask_sqlalchemy.Model" in base_cl:
            model_cls.append(cls)

model_forms = list()
for model in model_cls:
    for form in form_cls:
        if "%sform" % model.__name__.lower() == form.__name__.lower():
            model_forms.append((model, form))
            
for model, form in model_forms:
    name = model.__name__.lower()
    main.add_url_rule('/view/%s/' % name, view_func=ListView.as_view("view_%s" % name, model))
    main.add_url_rule('/add/%s/' % name, view_func=AddView.as_view("add_%s" % name, form, model))
    main.add_url_rule('/edit/%s/<int:id>' % name, view_func=EditView.as_view("edit_%s" % name, model, form))
    main.add_url_rule('/delete/%s/<int:id>' % name, view_func=DeleteView.as_view("delete_%s" % name, model))
