import re

from pathlib import Path

import app
from sqlalchemy import Table, Column, Integer, String, ForeignKey
from sqlalchemy.orm import class_mapper, ColumnProperty
from sqlalchemy.orm.attributes import InstrumentedAttribute
from flask.ext.login import UserMixin
from . import db
from flask import current_app
from whoosh.index import create_in
from whoosh.writing import AsyncWriter
from whoosh import qparser, index
import whoosh.fields

class GenericModel(object):
    def _get_schema(self):
        try:
            return self.schema
        except AttributeError:
            pass
        self.schema = whoosh.fields.Schema()
        for field in self._get_indexable_columns():
            #if hasattr(getattr(self, field), "primary_key") and getattr(self, field).primary_key:
            if field == "id":
                self.schema.add("model_id", whoosh.fields.ID(unique=True, stored=True))
            elif field == "name":
                self.schema.add(field, whoosh.fields.TEXT(stored=True, field_boost=2.0))
            else:
                self.schema.add(field, whoosh.fields.TEXT(stored=True))
        self.schema.add("model_name", whoosh.fields.TEXT(stored=True))
        self.schema.add("model_type", whoosh.fields.TEXT(stored=True, field_boost=2.0))
        return self.schema

    def _get_indexable_columns(self):
        for field in self.__table__.c.keys():
            if self.__table__.c[field].name.endswith("_id"):
                yield field.replace("_id", "")
            else:
                yield field

    def _get_index(self):
        index_directory = "%s/%s" % (current_app.config.get("WHOOSH_BASE"), self.__class__.__name__)
        if not Path(index_directory).exists():
            Path(index_directory).mkdir()
        model_index = None
        if not index.exists_in(index_directory):
            return create_in(index_directory, self._get_schema())
        return index.open_dir(index_directory)
        
    def add_index(self):
        self.update_index()

    def search_index(self, search_term):
        model_index = self._get_index()
        schema = self._get_schema()
        fields = list()
        for field in self._get_indexable_columns():
            if field == "id":
                field = "model_id"
            value = getattr(self, field)
            # Do not search the primary key
            if not value.primary_key:
                fields.append(field)
        parser = qparser.MultifieldParser(fields, schema)
        query = parser.parse(search_term)
        with model_index.searcher() as searcher:
            results = searcher.search(query)
            for result in results:
                yield result

    def update_index(self, update_dependencies=True):
        model_index = self._get_index()
        attrs = dict()
        for field in self._get_indexable_columns():
            value = getattr(self, field)
            if field == "id":
                attrs["model_id"] = unicode(value)
            elif hasattr(value, "name"):
                attrs[field] = unicode(value.name.lower())
                attrs["_stored_" + field] = unicode(value.name)
            else:
                attrs[field] = unicode(getattr(self, field)).lower()
                attrs["_stored_" + field] = unicode(getattr(self, field))
        attrs["model_name"] = unicode(self.__class__.__name__)
        attrs["model_type"] = unicode(self.get_model_friendly_name().lower())
        with AsyncWriter(model_index) as writer:
            writer.update_document(**attrs)
            if update_dependencies:
                for model in self.get_dependencies():
                    model.update_index(update_dependencies=False)

    def delete_index(self):
        model_index = self._get_index()
        document = None
        with AsyncWriter(model_index) as writer:
            writer.delete_by_term("model_id", unicode(self.id))
        
    def get_columns(self, one_to_many=False, foreign_key=False):
        columns = [prop.key for prop in class_mapper(self.__class__).iterate_properties
                    if isinstance(prop, ColumnProperty)]
        columns += class_mapper(self.__class__).relationships.keys()
        if one_to_many:
            columns = class_mapper(self.__class__).relationships.keys()
        elif foreign_key:
            fk = list()
            for column in columns:
                class_columns = class_mapper(self.__class__).columns
                if column in class_columns.keys() and class_columns[column].foreign_keys:
                    fk.append(column)
            columns = fk
        if columns is None:
            columns = list()
        return columns

    def get_dependencies(self):
        """ Get the dependent objects """
        dependencies = list()
        for column in self.get_columns(one_to_many=True):
            attr = getattr(self, column)
            if hasattr(attr, "all"):
                dependencies += attr.all()
        return dependencies


    def get_model_friendly_name(self):
        return re.sub("([a-z])([A-Z])","\g<1> \g<2>",self.__class__.__name__)

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

    def get_column_type(self, column):
        return getattr(type(self), column).property.columns[0].type
        
    def get_one_to_many_columns(self):
        return self.get_columns(one_to_many=True)

    def get_foreign_keys(self):
        return self.get_columns(foreign_key=True)

class Location(db.Model, GenericModel):
    __tablename__ = "Location"
    __doc__ = __tablename__
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    zip_code = db.Column(db.String(64))
    street_number = db.Column(db.String(32))
    country_id = db.Column(db.Integer, db.ForeignKey("Country.id"))
    county_id = db.Column(db.Integer, db.ForeignKey("County.id"))
    city_id = db.Column(db.Integer, db.ForeignKey("City.id"))
    street_id = db.Column(db.Integer, db.ForeignKey("Street.id"))
    system = db.relationship("System", backref="location", lazy="dynamic")
    display_fields = ["name", "street", "city", "country"]
    order_by = "name"
    cascade = [("country", "county", "city", "street")]
    def __repr__(self):
        return '<%s %r>' % (self.__class__.__name__, self.name)

class HardwareType(db.Model, GenericModel):
    __tablename__ = "HardwareType"
    __doc__ = __tablename__
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    hardware = db.relationship("Hardware", backref="hardware_type", lazy="dynamic")
    hardware_model = db.relationship("HardwareModel", backref="hardware_type", lazy="dynamic")
    display_fields = ["name"]
    order_by = "name"
    def __repr__(self):
        return '<%s %r>' % (self.__class__.__name__, self.name)

class Street(db.Model, GenericModel):
    __tablename__ = "Street"
    __doc__ = __tablename__
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    city_id = db.Column(db.Integer, db.ForeignKey("City.id"))
    location = db.relationship("Location", backref="street", lazy="dynamic")
    display_fields = ["name", "city"]
    order_by = "name"
    def __repr__(self):
        return '<%s %r>' % (self.__class__.__name__, self.name)


class City(db.Model, GenericModel):
    __tablename__ = "City"
    __doc__ = __tablename__
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    county_id = db.Column(db.Integer, db.ForeignKey("County.id"))
    street = db.relationship("Street", backref="city", lazy="dynamic")
    location = db.relationship("Location", backref="city", lazy="dynamic")
    display_fields = ["name", "county"]
    order_by = "name"
    def __repr__(self):
        return '<%s %r>' % (self.__class__.__name__, self.name)


class County(db.Model, GenericModel):
    __tablename__ = "County"
    __doc__ = __tablename__
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    country_id = db.Column(db.Integer, db.ForeignKey("Country.id"))
    city = db.relationship("City", backref="county", lazy="dynamic")
    location = db.relationship("Location", backref="county", lazy="dynamic")
    display_fields = ["name", "country"]
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
    location = db.relationship("Location", backref="country", lazy="dynamic")
    display_fields = ["name"]
    order_by = "name"
    def __repr__(self):
        return '<%s %r>' % (self.__class__.__name__, self.name)


class L2Domain(db.Model, GenericModel):
    __tablename__ = "L2Domain"
    __doc__ = "Layer 2 Domain"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    description = db.Column(db.Text(255), unique=False)
    system = db.relationship("System", backref="l2domain", lazy="dynamic")
    display_fields = ["name"]
    order_by = "name"
    
    def __repr__(self):
        return '<%s %r>' % (self.__class__.__name__, self.name)

class L3Domain(db.Model, GenericModel):
    __tablename__ = "L3Domain"
    __doc__ = "Layer 3 Domain"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    description = db.Column(db.Text(255), unique=False)
    system = db.relationship("System", backref="l3domain", lazy="dynamic")
    display_fields = ["name"]
    order_by = "name"
    
    def __repr__(self):
        return '<%s %r>' % (self.__class__.__name__, self.name)


class SystemCategory(db.Model, GenericModel):
    __tablename__ = "SystemCategory"
    __doc__ = "System Category"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    description = db.Column(db.Text(255), unique=False)
    image = db.Column(db.String(255), unique=False)
    system = db.relationship("System", backref="system_category", lazy="dynamic")
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
    system = db.relationship("System", backref="vendor", lazy="dynamic")
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
    description = db.Column(db.Text(255))
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
    coordinance = db.Column(db.String(64), unique=True)
    vendor_id = db.Column(db.Integer, db.ForeignKey("Vendor.id"))
    hardware_type_id = db.Column(db.Integer, db.ForeignKey("HardwareType.id"))
    hardware_model_id = db.Column(db.Integer, db.ForeignKey("HardwareModel.id"))
    notes = db.Column(db.Text(255))
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
    def __repr__(self):
        return '<%s %r>' % (self.__class__.__name__, self.name)

class SoftwareVersion(db.Model, GenericModel):
    __tablename__ = "SoftwareVersion"
    __doc__ = __tablename__
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    software_id = db.Column(db.Integer, db.ForeignKey("Software.id"))
    system = db.relationship("System", backref="software_version", lazy="dynamic")
    display_fields = ["software", "name"]
    order_by = "name"
    def __repr__(self):
        return '<%s %r>' % (self.__class__.__name__, self.name)

class System(db.Model, GenericModel):
    __tablename__ = "System"
    __doc__ = __tablename__
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    l3domain_id = db.Column(db.Integer, db.ForeignKey("L3Domain.id"))
    management_ip = db.Column(db.String(64))
    description = db.Column(db.Text(255), unique=False)
    system_category_id = db.Column(db.Integer, db.ForeignKey("SystemCategory.id"))
    l2domain_id = db.Column(db.Integer, db.ForeignKey("L2Domain.id"))
    vendor_id = db.Column(db.Integer, db.ForeignKey("Vendor.id"))
    software_id = db.Column(db.Integer, db.ForeignKey("Software.id"))
    location_id = db.Column(db.Integer, db.ForeignKey("Location.id"))
    software_version_id = db.Column(db.Integer, db.ForeignKey("SoftwareVersion.id"))
    hardware = db.relationship("Hardware", secondary=systems_hardware, backref="system", lazy="dynamic")
    display_fields = ["name", "management_ip", "l2domain", "software", "software_version"]
    cascade = [("vendor", "software", "software_version")]
    order_by = "name"
    def __repr__(self):
        return '<%s %r>' % (self.__class__.__name__, self.name)

class User(UserMixin, db.Model):
    __tablename__ = "User"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)

    def verify_password(self, password):
        return True

