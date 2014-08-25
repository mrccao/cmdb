import os
from app import create_app
from app.extensions import celery

app = create_app(os.getenv('FLASK_CONFIG') or 'default')

if __name__ == '__main__':
    with app.app_context():
        celery.start()
