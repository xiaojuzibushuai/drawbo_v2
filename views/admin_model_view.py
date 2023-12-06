# -*- coding:utf-8 -*-

from flask import flash
from flask_admin.contrib.sqla import ModelView
from flask_security import current_user
from werkzeug.security import generate_password_hash
from flask_admin.babel import gettext


class AdminModelView(ModelView):

    def is_accessible(self):
        return current_user.is_authenticated


class UserModelView(AdminModelView):
    column_exclude_list = ['password']
    column_list = ['username', 'active', 'email', 'roles', 'confirmed_at']
    column_labels = {'username': '用户', 'active': '是否激活', 'email': '邮箱', 'roles': '权限'}
    column_searchable_list = ['username']
    form_columns = ['username', 'roles', 'password', 'email', 'active']
    column_descriptions = {
        'password': '注：修改密码直接删除原有密码并输入，系统会再次生成加密密码。',
        'active': '注：未激活的用户不能进行登录。'
    }
    can_view_details = True
    can_export = True
    page_size = 20

    def is_accessible(self):
        if current_user.has_role('admin'):
            return True
        else:
            return False

    def on_model_change(self, form, user, is_created):
        if is_created:
            user.password = generate_password_hash(form.password.data)

    def before_model_change(self, form, model):
        if form.password.data != model.password:
            form.password.data = generate_password_hash(form.password.data)

    def update_model(self, form, model):
        try:
            self.before_model_change(form, model)
            form.populate_obj(model)
            self._on_model_change(form, model, False)
            self.session.commit()
        except Exception as ex:
            if not self.handle_view_exception(ex):
                flash(gettext('Failed to update record. %(error)s', error=str(ex)), 'error')
            self.session.rollback()
            return False
        else:
            self.after_model_change(form, model, False)
        return True


class RoleModelView(AdminModelView):

    column_searchable_list = ['name', 'description']

    def is_accessible(self):
        if current_user.has_role('admin'):
            return True
        else:
            return False

    def get_query(self):
        if current_user.has_role('admin'):
            return super(RoleModelView, self).get_query()
        return super(RoleModelView, self).get_query().filter(False)

    def get_count_query(self):
        if current_user.has_role('admin'):
            return super(RoleModelView, self).get_count_query().filter(False)
        return super(RoleModelView, self).get_count_query().filter(False)
