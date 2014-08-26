from flask import Flask
from config import config
from .extensions import bootstrap, mail, moment, \
                        login_manager, pagedown
from flask.ext.sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def create_app(config_name):
    app = Flask(__name__)
    register_configuration(app, config_name)
    register_extensions(app)
    register_blueprints(app)
    return app

def register_configuration(app, config_name):
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
 
def register_blueprints(app):
    from .main import main as main_blueprint
    from .auth import auth as auth_blueprint
    from .api_1_0 import api as api_1_0_blueprint
    app.register_blueprint(main_blueprint)
    app.register_blueprint(auth_blueprint, url_prefix='/auth')
    app.register_blueprint(api_1_0_blueprint, url_prefix='/api/v1.0')

def register_extensions(app):
    bootstrap.init_app(app)
    mail.init_app(app)
    moment.init_app(app)
    db.init_app(app)
    login_manager.init_app(app)
    pagedown.init_app(app)
    if not app.debug and not app.testing and not app.config['SSL_DISABLE']:
        from flask.ext.sslify import SSLify
        sslify = SSLify(app)

