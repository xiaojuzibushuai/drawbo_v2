# -*- coding:utf-8 -*-

from flask_admin.contrib.sqla import ModelView
from flask_security import current_user
from models.course import Course
from sys_utils import app


class IndexRecommendView(ModelView):
    """
    首页推荐视图
    """
    column_list = ['course', 'active', 'priority', 'uptime']
    column_labels = {
        'active': '是否推荐',
        'course': '课程',
        'priority': '推荐优先级',
        'uptime': '更新时间'
    }
    form_columns = ['course', 'active', 'priority']
    column_searchable_list = ['course.title']
    column_filters = ['course.title']
    can_view_details = False
    can_create = True
    can_edit = True
    can_delete = True
    column_editable_list = ['active', 'priority']

    def is_accessible(self):
        return current_user.is_authenticated and current_user.has_role('admin')
