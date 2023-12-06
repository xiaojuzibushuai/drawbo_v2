# -*- coding:utf-8 -*-

from flask_admin.contrib.sqla import ModelView
from flask_security import current_user
from jinja2 import Markup
from flask import url_for, flash
import os
from flask_admin import form
from models.course import DeviceCategory
from models.device import Device
from sys_utils import db
from werkzeug.utils import secure_filename
import time


# 设置缩略图
def _list_thumbnail(view, context, model, name):
    if not model.save_path:
        return ''
    return Markup('<img style="height: 60px" src="%s">' % url_for('static', filename=model.save_path))


class CategoryView(ModelView):
    """
    课程分类视图
    """
    column_list = ['title', 'detail', 'save_path', 'index_cate', 'priority', 'uptime']
    column_labels = {
        'title': '标题',
        'detail': '简介',
        'save_path': '图片地址',
        'index_cate': '是否在首页展现',
        'priority': '优先级',
        'uptime': '更新时间'
    }
    form_columns = ['title', 'detail', 'save_path', 'index_cate', 'priority']
    column_searchable_list = ['title']
    column_filters = ['title']
    can_view_details = False
    can_create = True
    can_edit = True
    can_delete = True
    column_editable_list = ['priority']

    form_choices = {
        'index_cate': (('0', '不展现'), ('1', '展现')),
    }

    column_formatters = {
        'save_path': _list_thumbnail,
        'index_cate': lambda v, c, m, p: '展现' if m.index_cate else '不展现',
    }
    file_path = os.path.abspath('.') + os.sep + 'static'
    form_extra_fields = {
        'save_path': form.ImageUploadField('图片', base_path=file_path, relative_path='category/', namegen=lambda o, f: secure_filename(str(int(time.time()))+os.path.splitext(f.filename)[1]))
    }

    def is_accessible(self):
        return current_user.is_authenticated and current_user.has_role('admin')

    def after_model_change(self, form, model, is_created):
        # 新建分类时同步至其它设备并置默认锁住
        if is_created:
            device_list = Device.query.filter_by(is_auth=1).all()
            for device in device_list:
                dc = DeviceCategory.query.filter_by(category_id=model.id, device_id=device.id).first()
                if not dc:
                    device_category = DeviceCategory(
                        category_id=model.id,
                        device_id=device.id
                    )
                    db.session.add(device_category)
                    db.session.commit()
