# -*- coding:utf-8 -*-

from flask_admin.contrib.sqla import ModelView
from flask_security import current_user


class DeviceCourseView(ModelView):
    """
    设备课程管理视图
    """
    column_list = ['id', 'device.deviceid', 'course.title', 'use_count']
    column_labels = {
        'device.deviceid': '设备',
        'course.title': '课程',
        'device': '设备',
        'course': '课程',
        'use_count': '使用次数'
    }
    form_columns = ['device', 'course', 'use_count']
    column_searchable_list = ['device.deviceid', 'course.title']
    column_filters = ['device.deviceid', 'course.title', 'use_count']
    column_editable_list = ['use_count']
    column_sortable_list = ['device.deviceid']
    can_view_details = True
    can_edit = True
    can_delete = True

    def is_accessible(self):
        return current_user.is_authenticated and current_user.has_role('admin')
