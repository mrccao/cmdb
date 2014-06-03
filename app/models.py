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
    def get_columns(self):
        columns = self.metadata.tables.get(self.__class__.__name__).columns.keys()
        columns = columns + self.get_one_to_many_columns()
        return columns
        
    def get_column(self, name):
        value = getattr(self, name)
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
        one_to_many_columns = list()
        for column in dir(self):
            if getattr(self, column).__class__.__name__ == "AppenderBaseQuery":
                one_to_many_columns.append(column)
        return one_to_many_columns

class Address(db.Model, GenericModel):
    __tablename__ = "Address"
    __doc__ = __tablename__
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    zipcode = db.Column(db.String(64), unique=True)
    order_by = "name"
    def __repr__(self):
        return '<%s %r>' % (self.__class__.__name__, self.name)

class HardwareType(db.Model, GenericModel):
    __tablename__ = "HardwareType"
    __doc__ = __tablename__
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    hardware_model_id = db.Column(db.Integer, db.ForeignKey("HardwareModel.id"))
    order_by = "name"
    def __repr__(self):
        return '<%s %r>' % (self.__class__.__name__, self.name)

class County(db.Model, GenericModel):
    __tablename__ = "County"
    __doc__ = __tablename__
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    country = db.relationship("Country", backref="country_county", lazy="dynamic")
    hardware_id = db.Column(db.Integer, db.ForeignKey("Hardware.id"))
    order_by = "name"
    def __repr__(self):
        return '<%s %r>' % (self.__class__.__name__, self.name)

class Country(db.Model, GenericModel):
    __tablename__ = "Country"
    __doc__ = __tablename__
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    code = db.Column(db.String(64), unique=True)
    county_id = db.Column(db.Integer, db.ForeignKey("County.id"))
    hardware_id = db.Column(db.Integer, db.ForeignKey("Hardware.id"))
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
    order_by = "name"
    
    def __repr__(self):
        return '<%s %r>' % (self.__class__.__name__, self.name)


class Hardware(db.Model, GenericModel):
    __tablename__ = "Hardware"
    __doc__ = __tablename__
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    vendor = db.relationship("Vendor", backref="vendor_hardware", lazy="dynamic")
    system = db.relationship("System", backref="system_hardware", lazy="dynamic")
    hardwaremodel = db.relationship("HardwareModel", backref="hardware_model_hardware", lazy="dynamic")
    county = db.relationship("County", backref="county_hardware", lazy="dynamic")
    country = db.relationship("Country", backref="country_hardware", lazy="dynamic")
    notes = db.Column(db.String(255), unique=False)
    order_by = "name"
    def __repr__(self):
        return '<%s %r>' % (self.__class__.__name__, self.name)

class HardwareModel(db.Model, GenericModel):
    __tablename__ = "HardwareModel"
    __doc__ = "Hardware Model"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    description = db.Column(db.String(255))
    vendor = db.relationship("Vendor", backref="vendor_hardware_model", lazy="dynamic")
    hardwaretype = db.relationship("HardwareType", backref="hardware_type_hardware", lazy="dynamic")
    hardware_id = db.Column(db.Integer, db.ForeignKey("Hardware.id"))
    order_by = "name"
    def __repr__(self):
        return '<%s %r>' % (self.__class__.__name__, self.name)

class Vendor(db.Model, GenericModel):
    __tablename__ = "Vendor"
    __doc__ = __tablename__
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    hardware_id = db.Column(db.Integer, db.ForeignKey("Hardware.id"))
    hardware_model_id = db.Column(db.Integer, db.ForeignKey("HardwareModel.id"))
    order_by = "name"
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
    order_by = "name"
    def __repr__(self):
        return '<%s %r>' % (self.__class__.__name__, self.name)

