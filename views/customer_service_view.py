# -*- coding:utf-8 -*-

from flask_admin.contrib.sqla import ModelView
from flask_security import current_user


class CustomerServiceView(ModelView):
    """
    客服管理
    """
    column_list = ['phone', 'active']
    column_labels = {
        'phone': '客服电话',
        'active': '是否激活'
    }
    form_columns = ['phone', 'active']
    column_searchable_list = ['phone']
    column_filters = ['phone']
    column_editable_list = ['active']
    can_view_details = True
    can_edit = True
    can_delete = True

    def is_accessible(self):
        return current_user.is_authenticated and current_user.has_role('admin')
