# -*- coding:utf-8 -*-

from flask_admin.contrib.sqla import ModelView
from flask_security import current_user
from jinja2 import Markup
from flask import url_for, flash
import os
from flask_admin import form
from werkzeug.utils import secure_filename
import time
from script.mosquitto_product import user_remove


# 设置缩略图
def _list_thumbnail(view, context, model, name):
    if not model.head:
        return ''
    return Markup('<img style="height: 60px" src="%s">' % url_for('static', filename=model.head))


class FaceInfoView(ModelView):
    """
    人脸信息视图
    """
    column_list = ['nickname', 'sex', 'head', 'device_info.deviceid', 'status', 'uptime']
    column_labels = {
        'nickname': '用户昵称',
        'sex': '性别',
        'status': '上课状态',
        'head': '头像',
        'device_info.deviceid': '设备',
        'uptime': '绑定时间'
    }
    form_columns = ['nickname', 'sex', 'status']
    column_searchable_list = ['nickname']
    column_filters = ['nickname', 'device_info.deviceid']
    can_view_details = False
    can_create = False
    can_edit = True
    can_delete = True
    form_choices = {
        'sex': (('0', '男'), ('1', '女')),
        'status': (('0', '未参与上课'), ('1', '参与上课'))
    }
    form_args = {
        'status': {
            'description': '<font style="color:#c12e2a">与手机选中学生上课操作一致</font>',
        }
    }
    column_editable_list = ['sex', 'status']
    # 格式化列表的图像显示
    column_formatters = {
        'head': _list_thumbnail,
        'sex': lambda v, c, m, p: '女' if m.sex else '男',
        'status': lambda v, c, m, p: '参与上课' if m.status else '未参与上课'
    }
    file_path = os.path.abspath('.') + os.sep + 'static'
    form_extra_fields = {
        'head': form.ImageUploadField('人脸照片', base_path=file_path, relative_path='face/', namegen=lambda o, f: secure_filename(str(int(time.time()))+os.path.splitext(f.filename)[1]))
    }

    def is_accessible(self):
        return current_user.is_authenticated and current_user.has_role('admin')

    def on_model_delete(self, model):
        """ 后台删除人脸信息后，需要下发到设备同步 """
        # flash('model id: %d' % model.id)
        user_remove(model.id)
