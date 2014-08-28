from flask import Markup
from flask.ext.wtf import Form
from wtforms import Field, StringField, TextAreaField, BooleanField, SelectField,\
    SubmitField, IntegerField, HiddenField, FileField, SelectMultipleField, DateField
from wtforms.validators import Required, Length, Email, Regexp, IPAddress
from wtforms import ValidationError 
import wtforms.widgets
from flask.ext.pagedown.fields import PageDownField
from ..models import L2Domain, L3Domain, System, Hardware, Vendor, HardwareModel, SystemCategory, Country, County, HardwareType, Software, SoftwareVersion, City, Street, Location


class Unique(object):
    """ validator that checks field uniqueness """
    def __init__(self, model, field, message=None):
        self.model = model
        self.field = field
        if not message:
            message = u'this element already exists'
        self.message = message

    def __call__(self, form, field):         
        check = self.model.query.filter(self.field == field.data).first()
        if "id" in form:
            id_type = type(form.id.data)
            if id_type in [int]:
                id = long(form.id.data)
            elif id_type in [str, unicode]:
                try:
                    id = long(form.id.data)
                except ValueError:
                    id = None
            else:
                id = form.id.data
        else:
            id = None
        if check and (id is None or id != check.id):
            raise ValidationError(self.message)

class BootstrapDateWidget(object):
    def __init__(self, data_date_viewmode="days", date_view_format="dd-mm-yyyy"):
        self.data_date_viewmode = data_date_viewmode
        self.date_view_format = date_view_format

    def __call__(self, field, **kwargs):
        data_date_viewmode = self.data_date_viewmode
        date_view_format = self.date_view_format
        kwargs['class'] = u'form-control date-picker'
        #kwargs['readonly'] = None
        html = u""
        html += u'<div class="input-group" >'
        html += u'<span class="input-group-addon">'
        html += u'<span class="glyphicon glyphicon-calendar"></span>'
        html += u'</span>'
        html += u'<input %s data-date-viewmode="%s" date-view-format="%s">' % (wtforms.widgets.html_params(**kwargs), data_date_viewmode, date_view_format)
        html += u'</div>'
        return html


class dDateField(DateField):
    widget = BootstrapDateWidget(data_date_viewmode="days", date_view_format="dd-mm-yyyy")


class mDateField(DateField):
    widget = BootstrapDateWidget(data_date_viewmode="months", date_view_format="dd-mm-yyyy")


class yDateField(DateField):
    widget = BootstrapDateWidget(data_date_viewmode="years", date_view_format="dd-mm-yyyy")


class HardwareTypeForm(Form):
    id = HiddenField()
    name = StringField('Hardware Type', validators=[Required(), Unique(HardwareType, HardwareType.name)])
    submit = SubmitField('Submit')


class LocationForm(Form):
    id = HiddenField()
    name = StringField('Location Name', validators=[Required()])
    zip_code = StringField('Zip Code')
    street_number = StringField('Street Number')
    country = SelectField('Country', coerce=int)
    county = SelectField('County', coerce=int)
    city = SelectField('City', coerce=int)
    street = SelectField('Street', coerce=int)
    submit = SubmitField('Submit')


class StreetForm(Form):
    id = HiddenField()
    name = StringField('Street', validators=[Required()])
    city = SelectField('City', coerce=int)
    submit = SubmitField('Submit')


class CityForm(Form):
    id = HiddenField()
    name = StringField('City', validators=[Required()])
    county = SelectField('County', coerce=int)
    submit = SubmitField('Submit')


class CountyForm(Form):
    id = HiddenField()
    name = StringField('County / Province / State', validators=[Required()])
    country = SelectField('Country', default=59,coerce=int)
    submit = SubmitField('Submit')


class CountryForm(Form):
    id = HiddenField()
    name = StringField('Name', validators=[Required(), Unique(Country, Country.name)])
    code = StringField('Code', validators=[Length(max=255)])
    submit = SubmitField('Submit')


class L2DomainForm(Form):
    id = HiddenField()
    name = StringField('Name', validators=[Required(), Unique(L2Domain, L2Domain.name)])
    description = StringField('Description', validators=[Length(max=255)])
    submit = SubmitField('Submit')


class L3DomainForm(Form):
    id = HiddenField()
    name = StringField('Name', validators=[Required(), Unique(L3Domain, L3Domain.name)])
    description = StringField('Description', validators=[Length(max=255)])
    submit = SubmitField('Submit')


class SystemCategoryForm(Form):
    id = HiddenField()
    name = StringField('Name', validators=[Required(), Unique(SystemCategory, SystemCategory.name)])
    description = StringField('Description', validators=[Length(max=255)])
    #image = FileField(u'Image File')
    submit = SubmitField('Submit')


class SystemForm(Form):
    id = HiddenField()
    name = StringField('System Name', validators=[Required(), Unique(System, System.name), Length(min=2, max=64)])
    l3domain = SelectField('Management IP Layer 3 Domain', coerce=int, validators=[Required()])
    management_ip = StringField('Mangement IP', validators=[Required(), IPAddress()])
    vendor = SelectField('Vendor', coerce=int)
    software = SelectField('Software', coerce=int)
    software_version = SelectField('SoftwareVersion', coerce=int)
    system_category = SelectField('SystemCategory', coerce=int)
    l2domain = SelectField('Layer 2 Domain', coerce=int)
    location = SelectField('Location', coerce=int)
    description = StringField('Description', validators=[Length(max=255)])
    submit = SubmitField('Submit')

class HardwareForm(Form):
    id = HiddenField()
    name = StringField('Serial Number', validators=[Required(), Unique(Hardware, Hardware.name), Length(min=2, max=64)])
    asset_tag = StringField('Asset Tag', validators=[Unique(Hardware, Hardware.asset_tag)])
    system = SelectMultipleField('System', coerce=int)
    vendor = SelectField('Vendor', coerce=int, )
    hardware_type = SelectField('HardwareType', coerce=int)
    hardware_model = SelectField('HardwareModel', coerce=int)
    eos = yDateField('End of Sale')
    eol = yDateField('End of Life')
    location = SelectField('Location', coerce=int, )
    coordinance = StringField('Location Coordinance', validators=[Required()])
    notes = StringField('Notes', validators=[Length(max=255)])
    submit = SubmitField('Submit')


class VendorForm(Form):
    id = HiddenField()
    name = StringField('Vendor Name', validators=[Required(), Unique(Vendor, Vendor.name), Length(min=2, max=64)])
    submit = SubmitField('Submit')


class SoftwareForm(Form):
    id = HiddenField()
    name = StringField('Software', validators=[Required(), Unique(Software, Software.name), Length(min=2, max=64)])
    vendor = SelectField('Vendor', coerce=int)
    submit = SubmitField('Submit')


class SoftwareVersionForm(Form):
    id = HiddenField()
    name = StringField('Software version', validators=[Required(), Unique(SoftwareVersion, SoftwareVersion.name), Length(min=1, max=64)])
    software = SelectField('Software', coerce=int)
    submit = SubmitField('Submit')


class HardwareModelForm(Form):
    id = HiddenField()
    name = StringField('Hardware Model Name', validators=[Required(), Unique(HardwareModel, HardwareModel.name), Length(min=2, max=64)])
    vendor = SelectField('Vendor', default=2, coerce=int)
    hardware_type = SelectField('HardwareType', coerce=int)
    description = StringField('Description', validators=[Length(max=255)])
    submit = SubmitField('Submit')

