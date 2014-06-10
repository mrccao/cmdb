import sys
import inspect

import MySQLdb

from flask import render_template, redirect, url_for, abort, flash, request,current_app, make_response
from flask.views import View
from flask.ext.login import login_required, current_user
from flask.ext.sqlalchemy import get_debug_queries
from . import main
from .forms import L2DomainForm, SystemForm, VendorForm, HardwareModelForm, HardwareForm, SystemCategoryForm, CountryForm, CountyForm, HardwareTypeForm
from .. import db
from ..models import L2Domain, System, Vendor, HardwareModel, Hardware, SystemCategory, County, Country, HardwareType
from .. import models
from . import forms
from wtforms.widgets import Select

@main.route('/', methods=['GET'])
def index():
    models = [L2Domain, System, Vendor, HardwareModel, Hardware, SystemCategory, Country, County, HardwareType]
    return render_template('index.html', models=models)

@main.route('/parent_child/<parent>/<child>/<parent_id>', methods=['GET', 'POST'])
def parent_child(parent, child, parent_id):
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
    for row in child_cls.query.filter(getattr(child_cls, parent).any(id=parent_id)):
        options += "<option parent='%s' value='%s'>%s</option>" % (parent_id, row.id, row.name)
    return options


@main.route('/delete/country/<id>', methods=['GET', 'POST'])
def delete_country(id):
    return generic_delete(id, Country())

@main.route('/delete/hardwaretype/<id>', methods=['GET', 'POST'])
def delete_hardwaretype(id):
    return generic_delete(id, HardwareType())

@main.route('/delete/county/<id>', methods=['GET', 'POST'])
def delete_county(id):
    return generic_delete(id, County())
    
@main.route('/delete/l2domain/<id>', methods=['GET', 'POST'])
def delete_l2domain(id):
    return generic_delete(id, System())

@main.route('/delete/systemcategory/<id>', methods=['GET', 'POST'])
def delete_systemcategory(id):
    return generic_delete(id, SystemCategory())

@main.route('/delete/system/<id>', methods=['GET', 'POST'])
def delete_system(id):
    return generic_delete(id, System())

@main.route('/delete/vendor/<id>', methods=['GET', 'POST'])
def delete_vendor(id):
    return generic_delete(id, Vendor())

@main.route('/delete/hardwaremodel/<id>', methods=['GET', 'POST'])
def delete_hardware_model(id):
    return generic_delete(id, HardwareModel())

@main.route('/add/county', methods=['GET', 'POST'])
def add_county():
    return generic_add(CountyForm(), County())

@main.route('/add/hardwaretype', methods=['GET', 'POST'])
def add_hardwaretype():
    return generic_add(HardwareTypeForm(), HardwareType())

@main.route('/add/country', methods=['GET', 'POST'])
def add_country():
    return generic_add(CountyForm(), County())

@main.route('/add/l2domain', methods=['GET', 'POST'])
def add_l2domain():
    return generic_add(L2DomainForm(), L2Domain())

@main.route('/add/systemcategory', methods=['GET', 'POST'])
def add_systemcategory():
    return generic_add(SystemCategoryForm(), SystemCategory())

@main.route('/add/system', methods=['GET', 'POST'])
def add_system():
    form = SystemForm()
    return generic_add(form, System())

@main.route('/add/vendor', methods=['GET', 'POST'])
def add_vendor():
    return generic_add(VendorForm(), Vendor())

@main.route('/add/hardwaremodel', methods=['GET', 'POST'])
def add_hardware_model():
    return generic_add(HardwareModelForm(), HardwareModel())

@main.route('/view/county', methods=['GET', 'POST'])
def view_county():
    return generic_view(County(),["name", "country"])

@main.route('/view/hardwaretype', methods=['GET', 'POST'])
def view_hardwaretype():
    return generic_view(HardwareType(),["name"])

@main.route('/view/country', methods=['GET', 'POST'])
def view_country():
    return generic_view(Country(),["name", "code"])

@main.route('/view/l2domain', methods=['GET', 'POST'])
def view_l2domain():
    return generic_view(L2Domain(),["name", "description"])

@main.route('/view/systemcategory', methods=['GET', 'POST'])
def view_systemcategory():
    return generic_view(SystemCategory(),["name"])

@main.route('/view/system', methods=['GET', 'POST'])
def view_system():
    return generic_view(System(),["name", "managementip", "l2domain"])

@main.route('/view/vendor', methods=['GET', 'POST'])
def view_vendor():
    return generic_view(Vendor(),["name"])

@main.route('/view/hardwaremodel', methods=['GET', 'POST'])
def view_hardwaremodel():
    return generic_view(HardwareModel(),["name", "vendor", "hardwaretype"])

@main.route('/edit/county/<id>', methods=['GET', 'POST'])
def edit_county(id):
    return generic_edit(id, County(), CountyForm())

@main.route('/edit/hardwaretype/<id>', methods=['GET', 'POST'])
def edit_hardwaretype(id):
    return generic_edit(id, HardwareType(), HardwareTypeForm())

@main.route('/edit/country/<id>', methods=['GET', 'POST'])
def edit_country(id):
    return generic_edit(id, Country(), CountryForm())

@main.route('/edit/l2domain/<id>', methods=['GET', 'POST'])
def edit_l2domain(id):
    return generic_edit(id, L2Domain(), L2DomainForm())

@main.route('/edit/systemcategory/<id>', methods=['GET', 'POST'])
def edit_systemcategory(id):
    return generic_edit(id, SystemCategory(), SystemCategoryForm())

@main.route('/edit/system/<id>', methods=['GET', 'POST'])
def edit_system(id):
    return generic_edit(id, System(), SystemForm())

@main.route('/edit/vendor/<id>', methods=['GET', 'POST'])
def edit_vendor(id):
    return generic_edit(id, Vendor(), VendorForm())

@main.route('/edit/hardwaremodel/<id>', methods=['GET', 'POST'])
def edit_hardware_model(id):
    return generic_edit(id, HardwareModel(), HardwareModelForm())

@main.route('/edit/hardware/<id>', methods=['GET', 'POST'])
def edit_hardware(id):
    return generic_edit(id, Hardware(), HardwareForm())

def populate_one_to_many_choices(form, model):
    # Fill in the form choices from the models
    for column in model.get_one_to_many_columns():
        related_model = getattr(model, column).column_descriptions[0]["type"]
        choices = [(r_column.id, getattr(r_column, related_model.order_by)) for r_column in related_model.query.order_by(related_model.order_by)]
        setattr(getattr(form, column), "choices", choices)
    return form

def update_row(form, model, add=False):
    changed = False
    for field in model.get_columns():
        if field in form.__dict__:
            if field in model.get_one_to_many_columns():
                related_model = getattr(model, field).column_descriptions[0]["type"]
                setattr(model, field, related_model.query.filter_by(id=getattr(form, field).data))
            else:
                setattr(model, field, getattr(form, field).data)
    if add:
        model.id = None
        db.session.add(model)
    db.session.commit()
    return True


def generic_add(form, model, cascade=None):
    form = populate_one_to_many_choices(form, model)
    if form.validate_on_submit():
        update_row(form, model, add=True)
        redirect_url = ".view_%s" % type(model).__name__.lower()
        return redirect(url_for(redirect_url))
    if cascade is None:
        cascade = list()
    return render_template('edit_model.html', form=form, Table=model, cascade=cascade)

def generic_edit(id, model, form, cascade=None):
    model = model.query.filter_by(id=id).first()
    form = populate_one_to_many_choices(form, model)
    redirect_url = ".view_%s" % type(model).__name__.lower()
    if form.validate_on_submit():
        update_row(form, model)
        return redirect(url_for(redirect_url))
    else:
        for field in model.get_columns():
            if field in form.__dict__:
                form_field = getattr(form, field)
                if field in model.get_one_to_many_columns():
                    if form_field.widget.__class__ == Select and form_field.widget.multiple:
                        form_field.data = map(lambda x: x.id, getattr(model, field))
                    else:
                        form_field.data = getattr(model, field)[0].id
                else:
                    form_field.data = getattr(model, field)
    if cascade is None:
        cascade = list()
    return render_template('edit_model.html', form=form, Table=type(model), cascade=cascade)

def generic_delete(id, model):
    row = model.query.filter_by(id=id).first()
    redirect_url = ".view_%s" % type(model).__name__.lower()
    db.session.delete(row)
    return redirect(url_for(redirect_url))

class AddView(View):
    methods = ['GET', 'POST']

    def __init__(self, form, model):
        self.model = model
        self.form = form

    def dispatch_request(self):
        cascade = []
        if hasattr(self.model, "cascade"):
            cascade = self.model.cascade
        return generic_add(self.form(), self.model(), cascade=cascade)

class DeleteView(View):
    methods = ['GET', 'POST']

    def __init__(self, model):
        self.model = model

    def dispatch_request(self, id):
        row = self.model.query.filter_by(id=id).first()
        name = self.model.__name__.lower()
        redirect_url = ".view_%s" % name
        db.session.delete(row)
        #return redirect(url_for(redirect_url))
        return redirect("/view/%s/" % name)


class ListView(View):
    methods = ['GET', 'POST']

    def __init__(self, model):
        self.model = model
        self.table_view = self._table_view(model, model.display_fields)
        self.table_view.records = model.query.order_by(self.table_view.order.by).all()
        if not self.table_view.order.asc:
            self.table_view.records.reverse()

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
                #print self.model.name.__class__.__name__ == "InstrumentedAttribute"
                print self.model.__class__
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
    mods = list()
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
    if "hardware" != name:
        continue
    main.add_url_rule('/add/%s/' % name, view_func=AddView.as_view("add_%s" % name, form, model))
    main.add_url_rule('/view/%s/' % name, view_func=ListView.as_view("view_%s" % name, model))
    main.add_url_rule('/delete/%s/<int:id>' % name, view_func=DeleteView.as_view("delete_%s" % name, model))

"""
@main.route('/add/hardware', methods=['GET', 'POST'])
def add_hardware():
    cascade = [(Vendor, HardwareModel)]
    return generic_add(HardwareForm(), Hardware(), cascade)

@main.route('/view/hardware', methods=['GET', 'POST'])
def view_hardware():
    return generic_view(Hardware(),["name", "system", "vendor", "hardwaremodel"])

@main.route('/delete/hardware/<id>', methods=['GET', 'POST'])
def delete_hardware(id):
    return generic_delete(id, Hardware())

"""


def generic_view(model, displayed_fields=None):
    class table_view:
        name = type(model).__name__
        displayed = displayed_fields
        #raise Exception()
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
    return render_template('view_model.html', Table=table_view)


