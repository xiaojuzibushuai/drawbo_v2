from datetime import datetime
from flask_security import UserMixin, RoleMixin
from sys_utils import db

# Define the User/Role model
admin_roles_users = db.Table('admin_roles_users',
                             db.Column('user_id', db.Integer(), db.ForeignKey('admin_users.id')),
                             db.Column('role_id', db.Integer(), db.ForeignKey('admin_roles.id')))


class AdminUser(db.Model, UserMixin):
    """ 系统管理员 """
    __tablename__ = 'admin_users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255))
    username = db.Column(db.String(255), unique=True)
    password = db.Column(db.String(225), nullable=False, server_default='')
    active = db.Column(db.Boolean())
    confirmed_at = db.Column(db.DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    roles = db.relationship('AdminRole',
                            secondary='admin_roles_users',
                            backref=db.backref('admin_users', lazy='dynamic'))

    # Flask-Login integration
    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return self.id

    # Required for administrative interface
    def __str__(self):
        return self.username


class AdminRole(db.Model, RoleMixin):
    """ 管理员权限 """
    __tablename__ = 'admin_roles'

    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    description = db.Column(db.String(255))

    def __str__(self):
        return self.description
