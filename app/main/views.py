import re
import sys
import inspect
import datetime

from flask import render_template, redirect, request, jsonify
from flask.views import View
from flask.ext.login import login_required
from flask_sqlalchemy import Model as SqlAlchemyModel
from . import main
from .forms import L2DomainForm, L3DomainForm, SystemForm, VendorForm, HardwareModelForm, HardwareForm, SystemCategoryForm, CountryForm, CountyForm, HardwareTypeForm, SoftwareForm, SoftwareVersionForm, CityForm, StreetForm, LocationForm
from .. import db
from ..models import L2Domain, L3Domain, System, Vendor, HardwareModel, Hardware, SystemCategory, County, Country, HardwareType, Software, SoftwareVersion, City, Street, Location
from jinja2.exceptions import TemplateNotFound
from whoosh.qparser import MultifieldParser

navbar = dict()
navbar["Organization"] = (Vendor,)
navbar["Domain"] = (L2Domain, L3Domain)
navbar["System"] = (System, SystemCategory)
navbar["Hardware"] = (Hardware, HardwareModel, HardwareType)
navbar["Software"] = (Software, SoftwareVersion)
navbar["Location"] = (Country, County, City, Street, Location)

related_info = dict()
related_info[System] = ((Hardware, ("hardware_type", "hardware_model", "name")),)

app_prefix = "/asset"

def pretty_print(text):
    text = re.sub("([a-z])([A-Z])","\g<1> \g<2>", text)
    return text.replace("_", " ")

@main.route('/', methods=['GET'])
#@login_required
def index():
    return render_template('index.html')

@main.route(app_prefix + "/models/", methods=['GET'])
def model_index():
    models = list()
    for model in get_model_classes():
        model = model.__name__.lower()
        models.append(model)
    return jsonify({'models': models })

@main.route(app_prefix + '/instant-search/', methods=['POST'])
#@login_required
def instant_search():
    results = list()
    search_term_original = request.form["search"]
    search_term_original = search_term_original.strip().strip("*")
    search_term = search_term_original.lower()
    if " " in search_term:
        for word in search_term.split():
            search_term = ("*%s*" % word).join(search_term.split(word))
    else:
        search_term = "*%s*" % search_term_original
    for model in get_model_classes():
        fields = list()
        for field in model()._get_indexable_columns():
            if field != "id":
                fields.append(field)
        fields.append("model_type")
        mparser = MultifieldParser(fields, schema=model()._get_schema())
        query = mparser.parse(search_term)
        with model()._get_index().searcher() as searcher:
            for h in searcher.search(query, terms=True):
                model_id, model_type, ci_name, score = h["model_id"], h["model_name"], h["name"], h.score
                matched_terms = list()
                for field, text in h.matched_terms():
                    field = "<code>%s</code>" % pretty_print(field)
                    for search_term_word in search_term_original.split():
                        text = ("<mark class='bg-danger'>%s</mark>" % search_term_word).join(text.split(search_term_word))
                    matched_terms.append(": ".join([field, text]))
                model_name = pretty_print(model_type)
                results.append((score, model_id, model_name, model_type, ci_name, matched_terms))
    results = sorted(results, key=lambda attr: attr[0], reverse=True)
    html_results = ""
    for score, model_id, model_name, model_type, ci_name, matched_terms in results:
        if model_id is None or model_id == u"None":
            continue
        html_results += "<tr>"
        html_results += '<td><a href="/assets/edit/%s/%s">%s</a></td>' % (model_type.lower(), model_id, model_name)
        html_results += '<td><a href="/assets/edit/%s/%s">%s</a></td>' % (model_type.lower(), model_id, ci_name)
        html_results += '<td><a href="/assets/edit/%s/%s">' % (model_type.lower(), model_id)
        for matched_term in matched_terms:
            html_results += "<p>" + matched_term + "</p>"
        html_results += "</a></td></tr>"
    return html_results


def get_model_from_string(model_string):
    model_string = model_string.replace("_", "")
    for name, cls in inspect.getmembers(sys.modules["app.models"]):
        name = name.lower()
        if name == model_string:
            return cls
 
@main.route(app_prefix + '/dependencies/<model>/<int:id>/', methods=['GET', 'POST'])
#@login_required
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


@main.route(app_prefix + '/parent_child/<parent>/<child>/<parent_id>/', methods=['GET', 'POST'])
#@login_required
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
        options.append(("null", -1L, "None"))
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
        if not choices:
            choices = [(-1L, "None")]
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

    #@login_required
    def dispatch_request(self):
        cascade = []
        if hasattr(self.model, "cascade"):
            cascade = self.model.cascade
        return AddView.generic_add(self.form(), self.model, cascade=cascade)

    @staticmethod
    def generic_add(form, model, cascade=None):
        model_type = model
        model_instance = model()
        form = populate_one_to_many_choices(form, model_instance)
        if form.validate_on_submit():
            AddView.update_row(form, model_instance, add=True)
            redirect_url = app_prefix + "/view/%s" % model_type.__name__.lower()
            return redirect(redirect_url)
        if cascade == None:
            cascade = list()
        template_name = 'edit_%s.html' % model_type.__name__.lower()
        for template in [template_name, "edit_model.html"]:
            try:
                return render_template(template, navbar_groups=navbar, model=model_instance, form=form, Table=model_instance, cascade=cascade)
            except TemplateNotFound:
                pass

def prepare_model_json(model_instance):
        """ Make a JSON friendly output of the model """
        item = dict()
        item["attr"] = list()
        item["model"]  = type(model_instance).__name__
        item["primary_key"]  = model_instance.id
        select_columns = model_instance.get_model_fields()
        base_fields = model_instance.get_base_fields()
        model_fields = model_instance.get_model_fields()
        for column in model_instance.get_columns():
            if column == "id":
                continue
            if column not in base_fields and column not in model_fields:
                continue
            attr = dict()
            attr["name"] = column
            if column in base_fields:
                attr["value"] = getattr(model_instance, column)
                attr["type"] = type(attr["value"]).__name__.lower()
            else:
                attr["value"] = getattr(model_instance, column).name
                attr["type"] = "select"
            attr["help"] = ""
            item["attr"].append(attr)
        return item
 
def camel_to_underscore(name):
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

class EditView(EditorView):

    @staticmethod
    def get_related_models(model_instance):
        model_type = type(model_instance)
        related = list()
        if model_type in related_info.keys():
            for r_model_type, columns in related_info[model_type]:
                r_model_type_column = camel_to_underscore(r_model_type.__name__)
                records = list()
                for r_model in getattr(model_instance, r_model_type_column).all():
                    r = list()
                    for column in columns:
                        if hasattr(getattr(r_model, column), "name"):
                            r.append(getattr(r_model, column).name)
                        else:
                            r.append(getattr(r_model, column))
                    records.append((r_model.id, r))
                related.append((r_model_type, columns, records))
        return related

 
    #@login_required
    def dispatch_request(self, id):
        cascade = []
        if hasattr(self.model, "cascade"):
            cascade = self.model.cascade
        return EditView.generic_edit(id, self.form(), self.model, cascade=cascade)

    @staticmethod
    def generic_edit(id, form, model, cascade=None):
        model_instance = model.query.filter_by(id=id).first()
        instances = list()
        columns = list()
        instance = prepare_model_json(model_instance)
        columns = model_instance.get_display_fields()
        return jsonify({'instance':instance})
 

class DeleteView(View):
    methods = ['GET', 'POST']

    def __init__(self, model):
        self.model = model

    #@login_required
    def dispatch_request(self, id):
        model_instance = self.model.query.filter_by(id=id).first()
        name = self.model.__name__.lower()
        redirect_url = ".view_%s" % name
        model_instance.delete_index()
        db.session.delete(model_instance)
        return jsonify({'status':'ok'})

class ListView(View):
    methods = ['GET', 'POST']

    def __init__(self, model):
        self.model = model

    #@login_required
    def dispatch_request(self):
        return ListView.generic_list(self.model())

    @staticmethod
    def generic_list(model, displayed_fields=None):
        instances = list()
        columns = list()
        for result in model.query.order_by("name").all():
            instances.append(prepare_model_json(result))
            if not columns:
                columns = result.get_display_fields()
        return jsonify({'columns': columns, 'instances':instances})
    
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
    main.add_url_rule(app_prefix + '/view/%s/' % name, view_func=ListView.as_view("view_%s" % name, model))
    main.add_url_rule(app_prefix + '/add/%s/' % name, view_func=AddView.as_view("add_%s" % name, form, model))
    main.add_url_rule(app_prefix + '/edit/%s/<int:id>/' % name, view_func=EditView.as_view("edit_%s" % name, form, model))
    main.add_url_rule(app_prefix + '/delete/%s/<int:id>/' % name, view_func=DeleteView.as_view("delete_%s" % name, model))
