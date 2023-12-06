# -*- coding:utf-8 -*-

from flask_admin.contrib.sqla import ModelView
from flask_security import current_user


class QRCodeSerialView(ModelView):
    """
    二维码管理视图
    """
    column_list = ['id', 'serial']
    column_labels = {'serial': '序列号'}
    column_searchable_list = ['serial']
    column_filters = ['serial']
    can_view_details = False
    can_create = False
    can_edit = False
    can_delete = True

    def is_accessible(self):
        return current_user.is_authenticated and current_user.has_role('admin')
