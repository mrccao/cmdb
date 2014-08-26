from celery import Celery
celery = Celery()

from flask.ext.bootstrap import Bootstrap
bootstrap = Bootstrap()

from flask.ext.mail import Mail
mail = Mail()

from flask.ext.moment import Moment
moment = Moment()

from flask.ext.login import LoginManager
login_manager = LoginManager()
login_manager.session_protection = 'strong'
login_manager.login_view = 'auth.login'

from flask.ext.pagedown import PageDown
pagedown = PageDown()
