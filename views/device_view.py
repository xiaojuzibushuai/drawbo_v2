# -*- coding:utf-8 -*-

from flask_admin.contrib.sqla import ModelView
from flask_security import current_user
from jinja2 import Markup
from flask import url_for


# 设置缩略图
def _list_thumbnail(view, context, model, name):
    if not model.qrcode_suffix_data:
        return ''
    return Markup('<img style="height: 60px" src="%s">' % url_for('static', filename=model.qrcode_suffix_data))


device_status = {'128': '空闲', '129': '暂停', '134': '关机', '144': '下载', '': '未知'}


class DeviceView(ModelView):
    """
    设备视图
    """
    column_list = ['deviceid', 'd_type', 'status', 'city', 'school', 'd_class', 'phone', 'qrcode_suffix_data', 'create_at', 'status_update', 'is_upgrade']
    column_labels = {
        'deviceid': '设备ID',
        'd_type': '版本',
        'status': '设备状态',
        'city': '城市',
        'school': '学校',
        'd_class': '班级',
        'phone': '管理员电话',
        'create_at': '上线时间',
        'status_update': '更新状态时间',
        'qrcode_suffix_data': '设备分享二维码',
        'is_upgrade': '是否需要升级'
    }
    form_columns = ['city', 'school', 'd_class', 'phone']
    column_searchable_list = ['deviceid', 'phone']
    column_filters = ['deviceid', 'city', 'school', 'd_class', 'phone']
    column_editable_list = ['d_type', 'is_upgrade']
    form_choices = {
        'd_type': (('1', '第一代'), ('2', '第二代')),
    }
    can_view_details = True
    can_create = False
    can_edit = True
    can_delete = False

    column_formatters = {
        'qrcode_suffix_data': _list_thumbnail,
        'status': lambda v, c, m, p: device_status[m.status] if m.status in device_status else '未知',
        'd_type': lambda v, c, m, p: '第一代' if m.d_type == 1 else '第二代'
    }

    def is_accessible(self):
        return current_user.is_authenticated and current_user.has_role('admin')
