from flask.ext.wtf import Form 
from wtforms import StringField, TextAreaField, BooleanField, SelectField,\
    SubmitField, IntegerField, HiddenField, FileField
from wtforms.validators import Required, Length, Email, Regexp, IPAddress
from wtforms import ValidationError 
from wtforms.widgets import Select, HiddenInput
from flask.ext.pagedown.fields import PageDownField
from ..models import L2Domain, System, Hardware, Vendor, HardwareModel, SystemCategory, Country, County, HardwareType


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

class HardwareTypeForm(Form):
    id = HiddenField()
    name = StringField('Hardware Type', validators=[Required(), Unique(HardwareType, HardwareType.name)])
    submit = SubmitField('Submit')


class CountyForm(Form):
    id = HiddenField()
    name = StringField('County / Province / State', validators=[Required(), Unique(County, County.name)])
    #default_country = Country.query.filter_by(code="DK").first().id
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

class SystemCategoryForm(Form):
    id = HiddenField()
    name = StringField('Name', validators=[Required(), Unique(SystemCategory, SystemCategory.name)])
    description = StringField('Description', validators=[Length(max=255)])
    image = FileField(u'Image File')
    submit = SubmitField('Submit')

class SystemForm(Form):
    id = HiddenField()
    name = StringField('System Name', validators=[Required(), Unique(System, System.name), Length(min=2, max=64)])
    management_ip = StringField('Mangement IP', validators=[Required(), Unique(System, System.name), IPAddress()])
    systemcategory = SelectField('SystemCategory', coerce=int)
    l2domain = SelectField('Layer 2 Domain', coerce=int)
    description = StringField('Description', validators=[Length(max=255)])
    submit = SubmitField('Submit')

class HardwareForm(Form):
    id = HiddenField()
    name = StringField('Serial Number', validators=[Required(), Unique(Hardware, Hardware.name), Length(min=2, max=64)])
    system = SelectField('System', coerce=int, widget=Select(multiple=True))
    vendor = SelectField('Vendor', coerce=int, )
    hardwaremodel = SelectField('HardwareModel', coerce=int)
    country = SelectField('Country', default=1, coerce=int)
    county = SelectField('County', coerce=int)
    notes = StringField('Notes', validators=[Length(max=255)])
    submit = SubmitField('Submit')

class VendorForm(Form):
    id = HiddenField()
    name = StringField('Vendor Name', validators=[Required(), Unique(Vendor, Vendor.name), Length(min=2, max=64)])
    submit = SubmitField('Submit')

class HardwareModelForm(Form):
    id = HiddenField()
    name = StringField('Hardware Model Name', validators=[Required(), Unique(HardwareModel, HardwareModel.name), Length(min=2, max=64)])
    #default_vendor = Vendor.query.filter_by(name="Cisco").first().id
    vendor = SelectField('Vendor', default=2, coerce=int)
    hardwaretype = SelectField('HardwareType', coerce=int)
    description = StringField('Description', validators=[Length(max=255)])
    submit = SubmitField('Submit')


