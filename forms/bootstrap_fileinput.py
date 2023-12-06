from wtforms.widgets import HTMLString, html_params
from wtforms import fields
from flask_admin._compat import urljoin
from flask import url_for
import json

from config import HOST


class FileInput(object):
    html_params = staticmethod(html_params)
    template = (
        '<div class="file-loading">'
        '<input %s class="file" type="file" multiple data-preview-file-type="any" data-upload-url="#" data-theme="fas">'
        '</div>'
    )

    def __call__(self, field, **kwargs):
        kwargs.setdefault('id', field.id)
        if 'value' not in kwargs:
            kwargs['value'] = field._value()
        return HTMLString(self.template % self.html_params(name=field.name, **kwargs))


class FileInputField(fields.StringField):
    widget = FileInput()

    def __init__(self, label=None, **kwargs):
        self.jsConf = True
        super(FileInputField, self).__init__(label=label, **kwargs)

    def bootstrap_fileinput_conf(self, field_name, pk, field_value=None, maxFileCount=20, minFileCount=0,
                                 uploadAsync='false', maxFileSize=20480, initialPreviewShowDelete='false',
                                 uploadUrl='', delUrl=None, showUpload='false', showRemove='false'):
        if delUrl is None:
            delUrl = url_for('.ajax_del_file')
        conf = {
            'id': 'input_%s' % field_name,
            'field_name': field_name,
            'uploadUrl': uploadUrl,
            'pk': pk,
            'maxFileCount': maxFileCount,
            'minFileCount': minFileCount,
            'uploadAsync': uploadAsync,
            'maxFileSize': maxFileSize,
            'initialPreviewShowDelete': initialPreviewShowDelete,
            'showUpload': showUpload,
            'showRemove': showRemove
        }
        if field_value is not None:
            preview_info = self.get_preview(field_value)
            if preview_info is not None:
                initialPreview = []
                initialPreviewConfig = []
                for title, link in preview_info:
                    initialPreview.append(urljoin(HOST, link))
                    initialPreviewConfig.append({
                        'caption': str(title),
                        'width': "30px",
                        'url': delUrl,
                        'key': int(pk),
                        'extra': {'link': str(link), 'field': field_name},
                        'type': 'audio'
                    })
                else:
                    conf['initialPreview'] = json.dumps(initialPreview)
                    conf['initialPreviewConfig'] = json.dumps(initialPreviewConfig)
        self.conf_option = conf

    def get_preview(self, field_value):
        latest = field_value.get('latest')
        if latest:
            return latest
        return None
