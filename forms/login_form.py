# -*- coding:utf-8 -*-

from wtforms import form, fields, validators
from werkzeug.security import check_password_hash
from sys_utils import db
from models.admin_user import AdminUser


class LoginForm(form.Form):
    username = fields.StringField('账号：', validators=[validators.required()])
    password = fields.PasswordField('密码：', validators=[validators.required()])

    def get_user(self):
        return db.session.query(AdminUser).filter(AdminUser.username == self.username.data).first()

    def validate_username(self, field):
        user = self.get_user()
        if user is None:
            raise validators.ValidationError('Invalid user')
        elif not user.active:
            raise validators.ValidationError('Inactive user')
        if not check_password_hash(user.password, self.password.data):
            raise validators.ValidationError('Invalid password')
