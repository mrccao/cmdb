class inspect_model_db(object):
    @staticmethod
    def column_exists(model, field):
        if field in model.__table__.columns.keys():
            return True
        return False

    @staticmethod
    def column_type(model, field):
        if inspect_model_db.column_exists(model, field):
            return type(model.__table__.columns[field].type).__name__
        return None

    @staticmethod
    def column_datetype(model, field):
        column_db_type = inspect_model_db.column_type(model, field)
        if column_db_type is None:
            return None
        return "date" in column_db_type.lower()

    @staticmethod
    def column_pk(model, field):
        if inspect_model_db.column_exists(model, field):
            return model.__table__.columns[field].primary_key
        return None

    @staticmethod
    def column_custom_type(model, field):
        if inspect_model_db.column_exists(model, field):
            info = model.__table__.columns[field].info
            if info is dict and "type" in info.keys():
                return info["type"]
        return None

    @staticmethod
    def column_ip_type(model, field):
        col_type = inspect_model_db.column_custom_type(model, field)
        if col_type == "ipaddress":
            return True
        return False
