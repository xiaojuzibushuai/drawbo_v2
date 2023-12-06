# -*- coding:utf-8 -*-

from flask_admin.contrib.sqla import ModelView
from flask_security import current_user


class DeviceCategoryView(ModelView):
    """
    设备分类管理视图
    """
    column_list = ['id', 'device.deviceid', 'category.title', 'lock']
    column_labels = {
        'device.deviceid': '设备',
        'category.title': '课程分类',
        'lock': '是否锁住',
        'device': '设备',
        'category': '课程分类'
    }
    form_columns = ['device', 'category', 'lock']
    column_searchable_list = ['device.deviceid', 'category.title']
    column_filters = ['device.deviceid', 'category.title', 'lock']
    column_editable_list = ['lock']
    column_sortable_list = ['device.deviceid']
    can_view_details = True
    can_edit = True
    can_delete = True

    def is_accessible(self):
        return current_user.is_authenticated and current_user.has_role('admin')
