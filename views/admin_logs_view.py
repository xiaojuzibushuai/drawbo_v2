# -*- coding:utf-8 -*-

from flask_admin.contrib.sqla import ModelView
from flask_security import current_user
from models.admin_logs import AdminLogs


class AdminLogsView(ModelView):
    """
    日志管理
    """
    can_create = False
    can_edit = False
    can_delete = False
    can_view_details = False
    can_export = True

    column_display_actions = False
    column_list = ['id', 'username', 'scope', 'message', 'ip', 'uptime']
    column_labels = {'id': 'ID', 'username': '用户', 'scope': '操作', 'message': '内容', 'ip': 'IP', 'uptime': '日期'}
    column_searchable_list = ('username', 'scope')
    
    def get_query(self):
        if current_user.has_role('admin'):
            return super(AdminLogsView, self).get_query().order_by(AdminLogs.id.desc())
        else:
            return super(AdminLogsView, self).get_query().filter(AdminLogs.username == current_user.username).order_by(AdminLogs.id.desc())

    def get_count_query(self):
        if current_user.has_role('admin'):
            return super(AdminLogsView, self).get_count_query()
        else:
            return super(AdminLogsView, self).get_count_query().filter(AdminLogs.username == current_user.username)

    def is_accessible(self):
        return current_user.is_authenticated
