from flask.ext.wtf import Form
from wtforms import Field, StringField, TextAreaField, BooleanField, SelectField,\
    SubmitField, IntegerField, HiddenField, FileField, SelectMultipleField
from wtforms.validators import Required, Length, Email, Regexp, IPAddress
from flask.ext.pagedown.fields import PageDownField
from ..models import L2Domain, L3Domain, System, Hardware, Vendor, HardwareModel, SystemCategory, Country, County, HardwareType, Software, SoftwareVersion, City, Street, Location
from .custom_fields import bDateField, IPv4Field
from .custom_field_validators import Unique


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
    #management_ip = StringField('Mangement IP', validators=[Required(), IPAddress()])
    management_ip = IPv4Field('Mangement IP', validators=[Required()])
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
    eos = bDateField('End of Sale', date_viewmode="years")
    eol = bDateField('End of Life', date_viewmode="years")
    description = StringField('Description', validators=[Length(max=255)])
    submit = SubmitField('Submit')


