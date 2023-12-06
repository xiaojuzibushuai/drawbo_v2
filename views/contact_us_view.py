# -*- coding:utf-8 -*-

from flask_admin.contrib.sqla import ModelView
from flask_security import current_user


class ContactUsView(ModelView):
    """
    联系我们视图
    """
    column_list = ['title', 'priority', 'uptime']
    column_labels = {
        'title': '标题',
        'content': '内容',
        'priority': '优先级',
        'uptime': '更新时间'
    }
    form_columns = ['title', 'content', 'priority']
    column_searchable_list = ['title']
    column_filters = ['title']
    column_editable_list = ['priority']
    can_view_details = True
    can_edit = True
    can_delete = True

    def is_accessible(self):
        return current_user.is_authenticated and current_user.has_role('admin')
