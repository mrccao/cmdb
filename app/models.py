from datetime import datetime
import hashlib
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from markdown import markdown
import bleach
from flask import current_app, request, url_for
from flask.ext.login import UserMixin, AnonymousUserMixin
from app.exceptions import ValidationError
from . import db, login_manager

class GenericModel(object):
    def get_columns(self, one_to_many=False, foreign_key=False):
        columns = list()
        model_type = type(self)
        for att in dir(model_type):
            if hasattr(getattr(model_type, att), "property"):
                if not one_to_many and not foreign_key:
                    columns.append(att)
                elif one_to_many and hasattr(getattr(model_type, att).property, "mapper"):
                    columns.append(att)
                if foreign_key and hasattr(getattr(model_type, att).property, "expression"):
                    if getattr(model_type, att).property.expression.foreign_keys:
                        columns.append(att)
        return columns
        
    def get_column(self, name):
        value = getattr(self, name)
        if value is None:
            raise Exception()
        if name in self.get_one_to_many_columns():
            try:
                value = value[0]
                if "name" not in dir(value):
                    value = value.get_columns()[0]
                else:
                    value = value.name
            except IndexError:
                value = None
        return value

    def get_one_to_many_columns(self):
        return self.get_columns(one_to_many=True)

    def get_foreign_keys(self):
        return self.get_columns(foreign_key=True)

class Address(db.Model, GenericModel):
    __tablename__ = "Address"
    __doc__ = __tablename__
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    zipcode = db.Column(db.String(64), unique=True)
    display_fields = ["name"]
    order_by = "name"
    def __repr__(self):
        return '<%s %r>' % (self.__class__.__name__, self.name)

class HardwareType(db.Model, GenericModel):
    __tablename__ = "HardwareType"
    __doc__ = __tablename__
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    hardware_model = db.relationship("HardwareModel", backref="hardware_type", lazy="dynamic")
    display_fields = ["name"]
    order_by = "name"
    def __repr__(self):
        return '<%s %r>' % (self.__class__.__name__, self.name)

class County(db.Model, GenericModel):
    __tablename__ = "County"
    __doc__ = __tablename__
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    country_id = db.Column(db.Integer, db.ForeignKey("Country.id"))
    display_fields = ["name"]
    order_by = "name"
    def __repr__(self):
        return '<%s %r>' % (self.__class__.__name__, self.name)

class Country(db.Model, GenericModel):
    __tablename__ = "Country"
    __doc__ = __tablename__
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    code = db.Column(db.String(64), unique=True)
    county = db.relationship("County", backref="country", lazy="dynamic")
    #hardware_id = db.Column(db.Integer, db.ForeignKey("Hardware.id"))
    display_fields = ["name"]
    order_by = "name"
    def __repr__(self):
        return '<%s %r>' % (self.__class__.__name__, self.name)


class L2Domain(db.Model, GenericModel):
    __tablename__ = "L2Domain"
    __doc__ = "Layer 2 Domain"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    description = db.Column(db.String(255), unique=False)
    system_id = db.Column(db.Integer, db.ForeignKey("System.id"))
    display_fields = ["name"]
    order_by = "name"
    
    def __repr__(self):
        return '<%s %r>' % (self.__class__.__name__, self.name)

class SystemCategory(db.Model, GenericModel):
    __tablename__ = "SystemCategory"
    __doc__ = "System Category"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    description = db.Column(db.String(255), unique=False)
    image = db.Column(db.String(255), unique=False)
    system_id = db.Column(db.Integer, db.ForeignKey("System.id"))
    display_fields = ["name"]
    order_by = "name"
    
    def __repr__(self):
        return '<%s %r>' % (self.__class__.__name__, self.name)


class Vendor(db.Model, GenericModel):
    __tablename__ = "Vendor"
    __doc__ = __tablename__
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    hardware_model = db.relationship("HardwareModel", backref="vendor", lazy="dynamic")
    hardware = db.relationship("Hardware", backref="vendor", lazy="dynamic")
    display_fields = ["name"]
    order_by = "name"
    def __repr__(self):
        return '<%s %r>' % (self.__class__.__name__, self.name)

class HardwareModel(db.Model, GenericModel):
    __tablename__ = "HardwareModel"
    __doc__ = "Hardware Model"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    description = db.Column(db.String(255))
    vendor_id = db.Column(db.Integer, db.ForeignKey("Vendor.id"))
    hardware = db.relationship("Hardware", backref="hardware_model", lazy="dynamic")
    hardware_type_id = db.Column(db.Integer, db.ForeignKey("HardwareType.id"))
    display_fields = ["name", "vendor_id", "hardware_type_id"]
    order_by = "name"
    def __repr__(self):
        return '<%s %r>' % (self.__class__.__name__, self.name)


class Hardware(db.Model, GenericModel):
    __tablename__ = "Hardware"
    __doc__ = __tablename__
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    hardware_model_id = db.Column(db.Integer, db.ForeignKey("HardwareModel.id"))
    system = db.relationship("System", backref="system_hardware", lazy="dynamic")
    vendor_id = db.Column(db.Integer, db.ForeignKey("Vendor.id"))
    #county = db.relationship("County", backref="county_hardware", lazy="dynamic")
    #country = db.relationship("Country", backref="country_hardware", lazy="dynamic")
    notes = db.Column(db.String(255), unique=False)
    order_by = "name"
    display_fields = ["name", "system", "vendor", "hardwaremodel"]
    cascade = [(Vendor, HardwareModel), (Country, County)]
    def __repr__(self):
        return '<%s %r>' % (self.__class__.__name__, self.name)

class System(db.Model, GenericModel):
    __tablename__ = "System"
    __doc__ = __tablename__
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    managementip = db.Column(db.String(64), unique=True)
    description = db.Column(db.String(255), unique=False)
    systemcategory = db.relationship("SystemCategory", backref="system_category_system", lazy="dynamic")
    l2domain = db.relationship("L2Domain", backref="system", lazy="dynamic")
    hardware_id = db.Column(db.Integer, db.ForeignKey("Hardware.id"))
    display_fields = ["name", "managementip", "l2domain"]
    order_by = "name"
    def __repr__(self):
        return '<%s %r>' % (self.__class__.__name__, self.name)

