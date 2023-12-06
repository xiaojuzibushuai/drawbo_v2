# -*- coding:utf-8 -*-

from flask_admin.contrib.sqla import ModelView
from flask_security import current_user
from jinja2 import Markup
from flask import url_for, flash
import os
from flask_admin import form
from werkzeug.utils import secure_filename
import time
from flask_ckeditor import CKEditorField


# 设置缩略图
def _list_thumbnail(view, context, model, name):
    if not model.img_files:
        return ''
    return Markup('<img style="height: 60px" src="%s">' % url_for('static', filename=model.img_files))


# 视频
def _list_video(view, context, model, name):
    if not model.video_files:
        return ''
    return Markup('<video style="height: 60px"><source src="%s" type="video/mp4"></video>' % url_for('static', filename=model.video_files))


class CourseIntroduceView(ModelView):
    """
    课程介绍视图
    """
    column_list = ['title', 'img_files', 'video_files', 'tx_video_id', 'status', 'priority', 'uptime']
    column_labels = {
        'title': '标题',
        'content': '内容',
        'img_files': '图片',
        'video_files': '视频',
        'status': '是否有效',
        'priority': '优先级',
        'uptime': '更新时间',
        'tx_video_id': '腾讯视频ID'
    }
    form_columns = ['title', 'content', 'img_files', 'video_files', 'tx_video_id', 'status', 'priority']
    column_searchable_list = ['title']
    column_filters = ['title']
    can_view_details = False
    can_create = True
    can_edit = True
    can_delete = True
    column_editable_list = ['priority', 'status']

    form_choices = {
        'status': (('0', '无效'), ('1', '有效')),
    }
    extra_js = ['https://cdn.ckeditor.com/4.20.2/standard/ckeditor.js']
    form_overrides = dict(content=CKEditorField)
    column_formatters = {
        'img_files': _list_thumbnail,
        'video_files': _list_video,
        'status': lambda v, c, m, p: '有效' if m.status else '无效'
    }
    file_path = os.path.abspath('.') + os.sep + 'static'
    form_extra_fields = {
        'img_files': form.ImageUploadField('图片', base_path=file_path, relative_path='introduce/', namegen=lambda o, f: secure_filename(str(int(time.time()))+os.path.splitext(f.filename)[1])),
        'video_files': form.FileUploadField('视频', base_path=file_path, relative_path='introduce/', namegen=lambda o, f: secure_filename(str(int(time.time()))+os.path.splitext(f.filename)[1]))
    }

    def is_accessible(self):
        return current_user.is_authenticated and current_user.has_role('admin')
