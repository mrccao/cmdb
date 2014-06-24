from datetime import datetime
import hashlib
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from sqlalchemy import Table, Column, Integer, String, ForeignKey, Sequence
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

    def get_related_model(self):        
        for column in self.__table__.foreign_keys:
            return getattr(type(self), column).property.mapper.primary_base_mapper.entity

    def display_column(self, name):
        """ Display a human friendly row column name """
        maximum_single_results = 3
        value = getattr(self, name)
        # if a related class then display the name of the related class
        if hasattr(type(value), "all"):
            results = list()
            for record in value.all():
                if len(results) > maximum_single_results:
                    results.append("...")
                    break
                results.append(record.name)
            value = ", ".join(results)
        elif hasattr(value, "__class__") and "InstrumentedList" in value.__class__.__name__:
            results = list()
            for record in value:
                if len(results) > maximum_single_results:
                    results.append("...")
                    break
                results.append(record.name)
            value = ", ".join(results)
        elif hasattr(type(value), "__bases__"):
            base_cls = [str(base_cls.__bases__) for base_cls in type(value).__bases__]
            for base_cl in base_cls:
                if "flask_sqlalchemy.Model" in base_cl:
                    value = value.name
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
    system = db.relationship("System", backref="l2domain", lazy="dynamic")
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
    software = db.relationship("Software", backref="vendor", lazy="dynamic")
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
    display_fields = ["name", "vendor", "hardware_type"]
    order_by = "name"
    def __repr__(self):
        return '<%s %r>' % (self.__class__.__name__, self.name)

systems_hardware = db.Table('systems_hardware',
        db.Column('system_id', db.Integer, db.ForeignKey('System.id')),
        db.Column('hardware_id', db.Integer, db.ForeignKey('Hardware.id'))
       )


class Hardware(db.Model, GenericModel):
    __tablename__ = "Hardware"
    __doc__ = __tablename__
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    asset_tag = db.Column(db.String(64), unique=True)
    hardware_model_id = db.Column(db.Integer, db.ForeignKey("HardwareModel.id"))
    vendor_id = db.Column(db.Integer, db.ForeignKey("Vendor.id"))
    notes = db.Column(db.String(255), unique=False)
    order_by = "name"
    display_fields = ["name", "system", "vendor"]
    cascade = [("vendor", "hardware_model"), ("country", "county")]
    def __repr__(self):
        return '<%s %r>' % (self.__class__.__name__, self.name)

class Software(db.Model, GenericModel):
    __tablename__ = "Software"
    __doc__ = __tablename__
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    software_version = db.relationship("SoftwareVersion", backref="software", lazy="dynamic")
    system = db.relationship("System", backref="software", lazy="dynamic")
    vendor_id = db.Column(db.Integer, db.ForeignKey("Vendor.id"))
    display_fields = ["name", "vendor"]
    order_by = "name"

class SoftwareVersion(db.Model, GenericModel):
    __tablename__ = "SoftwareVersion"
    __doc__ = __tablename__
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    software_id = db.Column(db.Integer, db.ForeignKey("Software.id"))
    system = db.relationship("System", backref="software_version", lazy="dynamic")
    display_fields = ["software", "name"]
    order_by = "name"
 
class System(db.Model, GenericModel):
    __tablename__ = "System"
    __doc__ = __tablename__
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    management_ip = db.Column(db.String(64), unique=True)
    description = db.Column(db.String(255), unique=False)
    system_category = db.relationship("SystemCategory", backref="system_category_system", lazy="dynamic")
    l2domain_id = db.Column(db.Integer, db.ForeignKey("L2Domain.id"))
    software_id = db.Column(db.Integer, db.ForeignKey("Software.id"))
    software_version_id = db.Column(db.Integer, db.ForeignKey("SoftwareVersion.id"))
    hardware = db.relationship("Hardware", secondary=systems_hardware, backref="system", lazy="dynamic")
    display_fields = ["name", "management_ip", "l2domain", "software", "software_version"]
    cascade = [("software", "software_version")]
    order_by = "name"
    def __repr__(self):
        return '<%s %r>' % (self.__class__.__name__, self.name)

