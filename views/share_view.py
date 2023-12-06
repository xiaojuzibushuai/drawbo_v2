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
    if not model.image_url:
        return ''
    return Markup('<img style="height: 60px" src="%s">' % url_for('static', filename=model.image_url))


class ShareView(ModelView):
    """
    小程序视图
    """
    column_list = ['title', 'path', 'image_url', 'isdel']
    column_labels = {
        'title': '标题',
        'path': '页面地址',
        'image_url': '图片',
        'isdel': '是否删除'
    }
    form_columns = ['title', 'path', 'image_url', 'isdel']
    column_searchable_list = ['title']
    column_filters = ['title', 'isdel']
    can_view_details = True
    can_create = True
    can_edit = True
    can_delete = True
    column_editable_list = ['isdel']
    column_descriptions = {'path': '页面path，必须是以/开头的完整路径'}

    column_formatters = {
        'image_url': _list_thumbnail,
    }
    file_path = os.path.abspath('.') + os.sep + 'static'
    form_extra_fields = {
        'image_url': form.ImageUploadField('图片', base_path=file_path, relative_path='index/', namegen=lambda o, f: secure_filename(str(int(time.time()))+os.path.splitext(f.filename)[1]))
    }

    def is_accessible(self):
        return current_user.is_authenticated and current_user.has_role('admin')
