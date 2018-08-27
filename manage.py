from flask_script import Manager, Server
from flask_migrate import Migrate, MigrateCommand
from kinetic_datanator.core import common_schema
from kinetic_datanator import app, db
# from app.server.model import User

migrate = Migrate(app, db)
manager = Manager(app)

# migrations
manager.add_command('migrate', MigrateCommand)
manager.add_command("runserver", Server(host='localhost'))

@manager.command
def create_db():
    """Creates the db tables."""
    db.create_all()

@manager.command
def drop_db():
    """Drops the db tables."""
    db.drop_all()


@manager.command
def restore_db():
    cs = common_schema.CommonSchema(restore_backup=True, clear_content=True, load_content=False, verbose=True)

# @manager.command
# def create_admin():
#     """Creates the admin user."""
#     db.session.add(User(username='admin', email='ad@min.com', password='admin', admin=True))
#     db.session.commit()


if __name__ == '__main__':
    manager.run()