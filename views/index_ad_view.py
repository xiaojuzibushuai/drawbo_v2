# -*- coding:utf-8 -*-

from flask_admin.contrib.sqla import ModelView
from flask_security import current_user
from jinja2 import Markup
from flask import url_for, flash
import os
from flask_admin import form
from werkzeug.utils import secure_filename
import time


# 设置缩略图
def _list_thumbnail(view, context, model, name):
    if not model.image:
        return ''
    return Markup('<img style="height: 60px" src="%s">' % url_for('static', filename=model.image))


class IndexADView(ModelView):
    """
    首页广告视图
    """
    column_list = ['title', 'image', 'url', 'position', 'active', 'priority', 'uptime']
    column_labels = {
        'title': '标题',
        'url': '链接页面地址',
        'image': '图片',
        'position': '位置',
        'active': '激活',
        'priority': '优先级',
        'uptime': '更新时间',
    }
    form_columns = ['title', 'image', 'url', 'position', 'active', 'priority']
    column_searchable_list = ['title']
    column_filters = ['title', 'position']
    can_view_details = False
    can_create = True
    can_edit = True
    can_delete = True
    column_editable_list = ['active', 'priority']

    column_formatters = {
        'image': _list_thumbnail,
    }
    file_path = os.path.abspath('.') + os.sep + 'static'
    form_extra_fields = {
        'image': form.ImageUploadField('图片', base_path=file_path, relative_path='index/', namegen=lambda o, f: secure_filename(str(int(time.time()))+os.path.splitext(f.filename)[1]))
    }

    def is_accessible(self):
        return current_user.is_authenticated and current_user.has_role('admin')
