#!/usr/bin/env python
import os

COV = None
if os.environ.get('FLASK_COVERAGE'):
    import coverage
    COV = coverage.coverage(branch=True, include='app/*')
    COV.start()

if os.path.exists('.env'):
    print('Importing environment from .env...')
    for line in open('.env'):
        var = line.strip().split('=')
        if len(var) == 2:
            os.environ[var[0]] = var[1]

from app import create_app, db
from app.models import L2Domain, L3Domain, System, Vendor, HardwareModel, Hardware, SystemCategory, Country, HardwareType, Software, SoftwareVersion, Location, City, County, Street
from flask.ext.script import Manager, Shell
from flask.ext.migrate import Migrate, MigrateCommand
import flask.ext.whooshalchemy

app = create_app(os.getenv('FLASK_CONFIG') or 'default')
manager = Manager(app)
migrate = Migrate(app, db)
with app.app_context():
    flask.ext.whooshalchemy.whoosh_index(app, System)
    flask.ext.whooshalchemy.whoosh_index(app, Location)
    flask.ext.whooshalchemy.whoosh_index(app, Hardware)
    flask.ext.whooshalchemy.whoosh_index(app, HardwareModel)
    flask.ext.whooshalchemy.whoosh_index(app, SoftwareVersion)


def make_shell_context():
    return dict(app=app, db=db, L2Domain=L2Domain, System=System, Vendor=Vendor, HardwareModel=HardwareModel, Hardware=Hardware, Country=Country, County=County, HardwareType=HardwareType, Software=Software, SoftwareVersion=SoftwareVersion, City=City, Street=Street, Location=Location, L3Domain=L3Domain)
manager.add_command("shell", Shell(make_context=make_shell_context))
manager.add_command('db', MigrateCommand)


@manager.command
def test(coverage=False):
    """Run the unit tests."""
    if coverage and not os.environ.get('FLASK_COVERAGE'):
        import sys
        os.environ['FLASK_COVERAGE'] = '1'
        os.execvp(sys.executable, [sys.executable] + sys.argv)
    import unittest
    tests = unittest.TestLoader().discover('tests')
    unittest.TextTestRunner(verbosity=2).run(tests)
    if COV:
        COV.stop()
        COV.save()
        print('Coverage Summary:')
        COV.report()
        basedir = os.path.abspath(os.path.dirname(__file__))
        covdir = os.path.join(basedir, 'tmp/coverage')
        COV.html_report(directory=covdir)
        print('HTML version: file://%s/index.html' % covdir)
        COV.erase()


@manager.command
def profile(length=25, profile_dir=None):
    """Start the application under the code profiler."""
    from werkzeug.contrib.profiler import ProfilerMiddleware
    app.wsgi_app = ProfilerMiddleware(app.wsgi_app, restrictions=[length],
                                      profile_dir=profile_dir)
    app.run()


@manager.command
def deploy():
    """ Run deployment tasks. """
    from flask.ext.migrate import upgrade

    # migrate database to latest revision
    upgrade()

    
    init_models = list()
    init_models.append((Vendor, ["Unknown", "Cisco", "Avaya", "HP"]))
    system_categories = (SystemCategory, ["Unknown", "Load Balancer", "Router", "Switch", "Firewall", "Server"])
    init_models.append(system_categories)
    init_models.append((L2Domain,["Unknown", "None","L2D"]))
    init_models.append((HardwareType,["Chassis", "Line Card", "Power Supply", "SFP"]))

    for model, init_items in init_models:
        for init_item in init_items:
            m = model()
            m.name = init_item
            db.session.add(m)

    db.session.commit()
    system = System()
    system.name = "Unknown"
    system.l2domain = L2Domain.query.first()
    sc = SystemCategory.query.filter_by(name="Unknown").first()
    system.system_category = sc
    db.session.add(system)

    software = Software()
    software.name = "IOS"
    software.vendor = Vendor.query.filter_by(name="Cisco").first()
    db.session.add(software)
    software = Software()
    software.name = "NXOS"
    software.vendor = Vendor.query.filter_by(name="Cisco").first()
    db.session.add(software)

    with open("iso-3166-2.txt", "r") as f:
        country_codes = f.readlines()

    country_codes.insert(0,"?? Unknown")

    for line in country_codes:
        line = line.split()
        code = line[0]
        country = " ".join(line[1::])
        c = Country()
        c.name = country
        c.code = code
        db.session.add(c)

    db.session.commit()


if __name__ == '__main__':
    manager.run()
