class inspect_model_db(object):
    @staticmethod
    def column_type(model, field):
        return type(model.__table__.columns[field].type).__name__

    @staticmethod
    def column_datetype(model, field):
        return "date" in inspect_model_db.column_type(model, field).lower()

    @staticmethod
    def column_pk(model, field):
        return model.__table__.columns[field].primary_key
