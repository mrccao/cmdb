from flask.ext.wtf import Form 
from wtforms import StringField, TextAreaField, BooleanField, SelectField,\
    SubmitField, IntegerField, HiddenField, FileField
from wtforms.validators import Required, Length, Email, Regexp, IPAddress
from wtforms import ValidationError 
from wtforms.widgets import Select, HiddenInput
from flask.ext.pagedown.fields import PageDownField
from ..models import L2Domain, System, Hardware, Vendor, HardwareModel, SystemCategory


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
    system_category = SelectField('SystemCategory', coerce=int)
    l2domain = SelectField('Layer 2 Domain', coerce=int)
    description = StringField('Description', validators=[Length(max=255)])
    submit = SubmitField('Submit')

class HardwareForm(Form):
    id = HiddenField()
    name = StringField('Serial Number', validators=[Required(), Unique(Hardware, Hardware.name), Length(min=2, max=64)])
    system = SelectField('System', coerce=int, widget=Select(multiple=True))
    vendor = SelectField('Vendor', coerce=int)
    hardware_model = SelectField('HardwareModel', coerce=int)
    notes = StringField('Notes', validators=[Length(max=255)])
    submit = SubmitField('Submit')

class VendorForm(Form):
    id = HiddenField()
    name = StringField('Vendor Name', validators=[Required(), Unique(Vendor, Vendor.name), Length(min=2, max=64)])
    submit = SubmitField('Submit')

class HardwareModelForm(Form):
    id = HiddenField()
    name = StringField('Hardware Model Name', validators=[Required(), Unique(HardwareModel, HardwareModel.name), Length(min=2, max=64)])
    vendor = SelectField('Vendor', coerce=int)
    description = StringField('Description', validators=[Length(max=255)])
    submit = SubmitField('Submit')


