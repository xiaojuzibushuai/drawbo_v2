# -*- coding:utf-8 -*-
import json
from urllib.parse import urljoin
from flask import flash, redirect, request, url_for, jsonify
from flask_admin import expose
from flask_admin.contrib.sqla import ModelView
from flask_admin.helpers import get_redirect_target
from flask_admin.model.helpers import get_mdict_item_or_list
from flask_security import current_user
from flask_admin.babel import gettext
from flask_admin.form import FormOpts, FileUploadField, ImageUploadField
from werkzeug.utils import secure_filename
from config import HOST
from forms.bootstrap_fileinput import FileInputField
from models.device import Device
from sys_utils import db
from models.course import DeviceCourse
import os
from jinja2 import Markup


# 设置缩略图
def _list_thumbnail(view, context, model, name):
    if not model.img_files:
        return ''
    return Markup('<img style="height: 60px" src="%s">' % url_for('static', filename=model.img_files))


class CourseView(ModelView):
    """
    课程视图
    """
    column_list = ['title', 'detail', 'save_path', 'category.title', 'index_show', 'priority', 'play_time',
                   'course_class', 'volume']
    column_labels = {
        'title': '课程标题',
        'detail': '课程简介',
        'save_path': '文件夹目录',
        'index_show': '是否显示',
        'priority': '优先级',
        'play_time': '播放时间',
        'course_class': '班级',
        'volume': '册别',
        'img_files': '课程图片',
        'data_files': 'dat后缀文件',
        'lrc_files': 'lrc后缀文件',
        'category': '课程类别',
        'category.title': '课程类别'
    }

    form_columns = ['title', 'detail', 'save_path', 'category', 'index_show', 'priority', 'play_time',
                    'course_class', 'volume', 'img_files', 'data_files', 'lrc_files', 'input_voice_files']
    column_searchable_list = ['title']
    column_filters = ['title', 'category.title']
    form_choices = {
        'course_class': (('小班', '小班'), ('中班', '中班'), ('大班', '大班')),
        'volume': (('上册', '上册'), ('下册', '下册')),
        'index_show': (('1', '是'), ('0', '否'))
    }
    form_extra_fields = {
        'input_voice_files': FileInputField('音频文件'),
        # 'input_video_files': FileInputField('视频文件'),
    }

    column_descriptions = {'save_path': '不支持修改文件夹名称'}

    column_editable_list = ['priority', 'play_time']
    column_sortable_list = ['title', 'detail', 'save_path', 'category.title', 'index_show', 'priority', 'play_time', 'course_class', 'volume']
    can_view_details = False
    can_create = True
    can_edit = True
    can_delete = True

    column_formatters = {
        'img_files': _list_thumbnail,
        'index_show': lambda v, c, m, p: '展现' if m.index_show else '不展现',
    }

    edit_template = 'course_edit.html'

    def is_accessible(self):
        return current_user.is_authenticated and current_user.has_role('admin')

    def after_model_change(self, form, model, is_created):
        if request.endpoint.endswith('.ajax_update'):
            return
        if is_created and form.save_path.data:
            file_path = os.path.abspath('.') + os.sep + 'static' + os.sep + 'upload' + os.sep + form.save_path.data
            # 创建目录
            if not os.path.exists(file_path):
                os.makedirs(file_path)
            # 同步课程至其它设备并且设次数为0次
            device_list = Device.query.filter_by(is_auth=1).all()
            for device in device_list:
                dc = DeviceCourse.query.filter_by(course_id=model.id, device_id=device.id).first()
                if not dc:
                    device_course = DeviceCourse(
                        course_id=model.id,
                        device_id=device.id
                    )
                    db.session.add(device_course)
                    db.session.commit()

    def after_model_delete(self, model):
        """ 删除课程后同时删除其它设备课程管理相关联的课程 """
        flash('model id: %d' % model.id)
        self.session.query(DeviceCourse).filter_by(course_id=None).delete()
        self.session.commit()

    @expose('/new/', methods=('GET', 'POST'))
    def create_view(self):
        """
            Create model view
        """
        self.form_widget_args = {'save_path': {'readonly': False}}
        return_url = get_redirect_target() or self.get_url('.index_view')

        if not self.can_create:
            return redirect(return_url)

        form = self.create_form()
        # 删除form不需要的字段
        del form.img_files
        del form.data_files
        del form.lrc_files
        del form.input_voice_files
        # del form.input_video_files
        if not hasattr(form, '_validated_ruleset') or not form._validated_ruleset:
            self._validate_form_instance(ruleset=self._form_create_rules, form=form)

        if self.validate_form(form):
            # in versions 1.1.0 and before, this returns a boolean
            # in later versions, this is the model itself
            model = self.create_model(form)
            if model:
                flash(gettext('Record was successfully created.'), 'success')
                if '_add_another' in request.form:
                    return redirect(request.url)
                elif '_continue_editing' in request.form:
                    # if we have a valid model, try to go to the edit view
                    if model is not True:
                        url = self.get_url('.edit_view', id=self.get_pk_value(model), url=return_url)
                    else:
                        url = return_url
                    return redirect(url)
                else:
                    # save button
                    # return redirect(self.get_save_return_url(model, is_created=True))
                    # 直接跳至编辑页面
                    return redirect(self.get_url('.edit_view', id=self.get_pk_value(model), url=return_url))

        form_opts = FormOpts(widget_args=self.form_widget_args,
                             form_rules=self._form_create_rules)

        if self.create_modal and request.args.get('modal'):
            template = self.create_modal_template
        else:
            template = self.create_template

        return self.render(template,
                           form=form,
                           form_opts=form_opts,
                           return_url=return_url)

    @expose('/edit/', methods=('GET', 'POST'))
    def edit_view(self):
        """
            Edit model view
        """
        if request.method == 'POST' and request.form.get('mode') == 'ajax':
            return self.ajax_upload(self.model)

        self.form_widget_args = {'save_path': {'readonly': True}}
        return_url = get_redirect_target() or self.get_url('.index_view')

        if not self.can_edit:
            return redirect(return_url)

        id = get_mdict_item_or_list(request.args, 'id')
        if id is None:
            return redirect(return_url)

        model = self.get_one(id)

        if model is None:
            flash(gettext('Record does not exist.'), 'error')
            return redirect(return_url)
        file_path = os.path.abspath('.') + os.sep + 'static'
        self.form_extra_fields = {
            # xiaojuzi update 2023922
            'img_files': ImageUploadField('图片', base_path=file_path, relative_path='upload/%s/' % model.save_path, namegen=lambda o, f: secure_filename(model.save_path+os.path.splitext(f.filename)[1]),allow_overwrite=True),
            'data_files': FileUploadField('dat文件', base_path=file_path, relative_path='upload/%s/' % model.save_path, namegen=lambda o, f: secure_filename(model.save_path+os.path.splitext(f.filename)[1]),allow_overwrite=True),
            'lrc_files': FileUploadField('lrc文件', base_path=file_path, relative_path='upload/%s/' % model.save_path, namegen=lambda o, f: secure_filename(model.save_path+os.path.splitext(f.filename)[1]),allow_overwrite=True),
            'input_voice_files': FileInputField('音频文件'),
            # 'input_video_files': FileInputField('视频文件'),
        }
        self._refresh_forms_cache()
        form = self.edit_form(obj=model)
        if not hasattr(form, '_validated_ruleset') or not form._validated_ruleset:
            self._validate_form_instance(ruleset=self._form_edit_rules, form=form)

        if self.validate_form(form):
            if self.update_model(form, model):
                flash(gettext('Record was successfully saved.'), 'success')
                if '_add_another' in request.form:
                    return redirect(self.get_url('.create_view', url=return_url))
                elif '_continue_editing' in request.form:
                    return redirect(request.url)
                else:
                    # save button
                    return redirect(self.get_save_return_url(model, is_created=False))

        if request.method == 'GET' or form.errors:
            self.on_form_prefill(form, id)
        self.conf_input_field(form, model)
        form_opts = FormOpts(widget_args=self.form_widget_args,
                             form_rules=self._form_edit_rules)

        if self.edit_modal and request.args.get('modal'):
            template = self.edit_modal_template
        else:
            template = self.edit_template

        return self.render(template,
                           model=model,
                           form=form,
                           form_opts=form_opts,
                           return_url=return_url)

    def ajax_upload(self, model):
        """
        boostrap-fileinput ajax_upload
        """
        delUrl = self.get_url('.ajax_del_file')
        field_name = request.form.get('field_name')
        pk_value = request.form.get('pk_value')
        m = self.session.query(model).get(pk_value)
        files = self.save_multi_file('input_%s' % field_name, m.save_path)
        if not files:
            ret_error = {'error': '只能上传mp3,wav格式的音频文件'}
            return jsonify(ret_error)
        if self.update_model_field(model, field_name, pk_value, files):
            ret_json = {
                'initialPreview': [
                    urljoin(HOST, link) for title, link in files
                ],
                'initialPreviewConfig': [
                    {'caption': title, 'width': "120px", 'url': delUrl, 'key': pk_value,
                     'extra': {'link': link, 'field': field_name}, 'type': 'audio'} for title, link in files
                ],
                'append': True
            }
            return jsonify(ret_json)

        ret_error = {'error': '上传失败'}
        return jsonify(ret_error)

    def update_model_field(self, model, field, pk, new_item):
        m = self.session.query(model).get(pk)
        field_value = getattr(m, field)
        if field_value:
            field_value = json.loads(field_value)
            if not field_value.get('latest'):
                field_value['latest'] = []
        else:
            field_value = {'latest': []}
        field_value['latest'].extend(new_item)
        field_value = json.dumps(field_value)
        setattr(m, field, field_value)
        self.session.commit()
        return True

    def save_multi_file(self, field, save_path):
        error = None
        ret = []
        file_path = os.path.abspath('.') + os.sep + 'static'
        uploadimg_folder, img_base_url = file_path, HOST
        if request.method == 'POST' and field in request.files:
            fileobjs = request.files.getlist('input_voice_files')
            for fileobj in fileobjs:
                fname = fileobj.filename
                pic_name = os.path.join('upload', str(save_path), str(fname))
                filepath = os.path.join(uploadimg_folder, pic_name)
                dirname = os.path.dirname(filepath)
                if not os.path.exists(dirname):
                    try:
                        path_ch(dirname)
                    except:
                        error = 'ERROR_CREATE_DIR'
                elif not os.access(dirname, os.W_OK):
                    error = 'ERROR_DIR_NOT_WRITEABLE'
                if not error:
                    fileobj.save(filepath)

                    file_size = os.path.getsize(filepath)
                    if file_size > 20 * 1024 * 1024:
                        error = '文件 "%s" 大于20M，请压缩后重新上传。' % fileobj.filename
                        self.delete_file(filepath)
                    else:
                        ret.append((fname, pic_name))

            return ret

    def before_model_change(self, form, model):
        if request.endpoint.endswith('.ajax_update'):
            return

    def on_model_change(self, form, model, is_created):
        if request.endpoint.endswith('.ajax_update'):
            return

    def conf_input_field(self, form, model):
        voice_files = None
        if model.voice_files:
            voice_files = json.loads(model.voice_files)
        form.input_voice_files.bootstrap_fileinput_conf(
            'voice_files', model.id,
            uploadUrl=self.get_url('.ajax_upload_view'),
            field_value=voice_files, maxFileCount=20
        )

    @expose('/ajax_upload', methods=['POST'])
    def ajax_upload_view(self):
        return self.ajax_upload(self.model)

    @expose('/ajax_del', methods=['POST'])
    def ajax_del_file(self):
        # s = json.dumps(dict(request.form.items()))
        pk = request.form.get('key')
        row = self.session.query(self.model).filter_by(id=pk).first()
        ret_error = {'error': '删除失败'}

        if row:
            field = request.form.get('field')
            arg_link = request.form.get('link')
            if not getattr(row, field):
                return jsonify(ret_error)

            field_value = json.loads(getattr(row, field))
            x = None
            for i, (title, link) in enumerate(field_value.get('latest')):
                if link == arg_link:
                    self.delete_file(link)
                    x = i
                    break
            if x is not None:
                field_value['latest'].pop(x)
                field_value = json.dumps(field_value, ensure_ascii=False)
                setattr(row, field, field_value)
                self.session.commit()
                ret = {'data': 'success'}
                return jsonify(ret)
        return jsonify(ret_error)

    def delete_file(self, filepath):
        print(filepath)
        UPLOADIMG_FOLDER = os.path.abspath('.') + os.sep + 'static'
        filepath = os.path.join(UPLOADIMG_FOLDER, filepath)
        if os.path.exists(filepath):
            os.remove(filepath)
            return True
        return False


def path_ch(path):
    if not os.path.exists(path):
        path_ch(os.path.split(path)[0])
        os.makedirs(path)
        os.chmod(path, 0o666)
