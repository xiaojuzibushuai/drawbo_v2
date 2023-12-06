# -*- coding:utf-8 -*-

from flask_admin.contrib.sqla import ModelView
from flask_security import current_user


class UserView(ModelView):
    """
    用户视图
    """
    column_list = ['openid', 'device_info.deviceid', 'uptime']
    column_labels = {
        'nickname': '用户昵称',
        'sex': '性别',
        'openid': 'openid',
        'phone': '手机',
        'device_info.deviceid': '设备',
        'uptime': '绑定时间',
        'device_info': '设备'
    }
    form_columns = ['nickname', 'sex', 'device_info']
    column_searchable_list = ['nickname', 'phone']
    column_filters = ['nickname', 'phone', 'device_info.deviceid']
    can_view_details = False
    can_create = False
    can_edit = True
    can_delete = True

    def is_accessible(self):
        return current_user.is_authenticated and current_user.has_role('admin')
