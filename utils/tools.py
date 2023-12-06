# -*- coding:utf-8 -*-

import hashlib
import secrets
import time
from datetime import datetime,timedelta

import bcrypt
from flask_security import current_user
from flask import request, jsonify
from pypinyin import pinyin, Style

from models.admin_logs import AdminLogs
from models.request_count import RequestCount
from sys_utils import db
from config import SIGN_KEY, ALLOWED_EXTENSIONS, HOST, MQ_HOST,  SMS_API_KEY
from collections.abc import Iterable
from functools import wraps
import logging
import random
import string
from utils.error_code import *
import qrcode
import os
import base64
import requests
from utils.face import FaceTool

def manager_app_logs(scope, message):
    """
    管理后台日志
    :param scope:       项目
    :param message:     操作记录
    :return:            Bool
    """
    username = "guest" if not current_user.is_authenticated else current_user.username
    ip = request.headers.get('X-Real-IP', request.remote_addr)
    logs = AdminLogs(scope=scope, username=username, ip=ip, message=message, uptime=datetime.datetime.now())
    db.session.add(logs)
    db.session.commit()
    return True


# 对象转字典 20231123 xiaojuzi
def model_to_dict(result)->dict:

    if not result:
        return {}
    # 转换完成后，删除  '_sa_instance_state' 特殊属性
    try:
        if isinstance(result, Iterable):
            if '__dict__' in dir(result[0]):
                tmp = [dict(zip(res.__dict__.keys(), res.__dict__.values())) for res in result]
                for t in tmp:
                    t.pop('_sa_instance_state')
            else:
                tmp = [dict(zip(res._asdict().keys(), res._asdict().values())) for res in result]
        else:
            if '__dict__' in dir(result):
                tmp = dict(zip(result.__dict__.keys(), result.__dict__.values()))
                tmp.pop('_sa_instance_state')
            else:
                tmp = dict(zip(result._asdict().keys(), result._asdict().values()))
        return tmp
    except BaseException as e:
        print(e.args)
        raise TypeError('Type error of parameter')


def dict_fill_url(dict_data, field_list):
    """
    补全字段里的资源路径
    :param dict_data: 字典或字典列表类型的数据
    :param field_list: 字段列表 list
    :return: dict_data
    """
    if isinstance(dict_data, list):
        for data in dict_data:
            for field in field_list:
                if field in data:
                    if data[field]:
                        data[field] = HOST + '/' + data[field]
    else:
        for field in field_list:
            if field in dict_data:
                if dict_data[field]:
                    dict_data[field] = HOST + '/' + dict_data[field]
    return dict_data


def dict_add_default_data(dict_data, **kwargs):
    """
    增加字段并设置指定值
    :param dict_data: 字典或字典列表类型的数据
    :param kwargs: 字段及设定值
    :return: dict_data
    """
    if isinstance(dict_data, list):
        for data in dict_data:
            data.update(kwargs)
    else:
        dict_data.update(kwargs)
    return dict_data


def change_field_key(dict_data, field_dict):
    """
    改变key
    :param dict_data: 字典或字典列表类型的数据
    :param field_dict: 字段字典 list
    :return: dict_data
    """
    if isinstance(dict_data, list):
        for data in dict_data:
            for k, v in field_dict.items():
                if k in data:
                    data[v] = data[k]
                    data.pop(k)
    else:
        for k, v in field_dict.items():
            if k in dict_data:
                dict_data[v] = dict_data[k]
                dict_data.pop(k)
    return dict_data


def dict_drop_field(dict_data, field_list):
    """
    删除字典或字典列表里的字段
    :param dict_data: 字典或字典列表类型的数据
    :param field_list: 字段列表 list
    :return: dict_data
    """
    if isinstance(dict_data, list):
        for data in dict_data:
            for field in field_list:
                if field in data:
                    data.pop(field)
    else:
        for field in field_list:
            if field in dict_data:
                dict_data.pop(field)
    return dict_data


def sign(form, rm=None):
    """
    验签
    :param form: http form data
    :param rm: 列表，列表中的字段不参与验签
    :return: Boolean
    """
    form_data = form.to_dict()
    if 'tk' not in form_data or 'ts' not in form_data:
        return TK_NOT_FIND
    # 过滤不参与验签字段
    if rm and isinstance(rm, list):
        for key in rm:
            if key in form_data:
                form_data.pop(key)
    ts = form_data.get('ts', '0000000000')
    tk = form_data.pop('tk')
    # 验签
    # 签名规则
    # 1、字典key首字母排序并使用|拼接
    # 2、sign_key拼接在后面
    # 3、md5签名
    st = '|'.join(['%s=%s' % (key, form_data[key]) for key in sorted(form_data)])
    st = '%s|%s' % (st, SIGN_KEY)
    current_tk = hashlib.md5(st.encode('utf8')).hexdigest()
    if current_tk == tk:
        # 检查timestamp是否过期(5min)
        if int(time.time()) > int(ts) + 300:
            return SIGN_INVALID
        else:
            return SUCCESS
    else:
        return SIGN_ERROR


def ret_data(errcode, data=None):
    if data:
        return {'errcode': errcode, 'msg': ERROR_CODE[errcode], 'data': data}
    else:
        return {'errcode': errcode, 'msg': ERROR_CODE[errcode]}

def iot_msg_manager(code, payload=None):
    """
    处理返回数据
    :param code:响应状态码
    :param payload:业务响应数据载体，不同的接口承载的数据结构不一样，若为空不返回
    :return:dict
    """
    if not payload:
        payload = {}
    res_dict = {'code': code}
    if code:
        res_dict['desc'] = ERROR_CODE[code]
    if len(payload):
        res_dict['payload'] = payload
    logging.info(res_dict)
    return res_dict


def create_noncestr(length=32):
    """产生随机字符串，不长于32位"""
    return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(length))


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


def decorator_sign(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        openid = request.form.get('openid', None)
        # 必填项
        if not openid:
            return jsonify(ret_data(PARAMS_ERROR))
        # 验签
        errcode = sign(request.form)
        if errcode != SUCCESS:
            return jsonify(ret_data(errcode))
        return f(*args, **kwargs)
    return decorated

# 定义装饰器实现某接口鉴权拿到令牌才能访问 xiaojuzi v2 20231129
def require_api_key(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        api_key = request.headers.get("X-API-Key")
        if api_key != SMS_API_KEY:
            return jsonify({"message": "Unauthorized"}), 401
        return func(*args, **kwargs)
    return wrapper

# 定义装饰器实现某接口访问频率限制 xiaojuzi v2 20231129
def rate_limit(interface_name, max_count,minutes):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            ip_address = request.remote_addr

            # 查询数据库中的记录
            request_count = db.session.query(RequestCount).filter_by(ip_address=ip_address,api_name=interface_name).first()

            if request_count:
                last_request_time = request_count.last_request_time
                elapsed_time = datetime.now() - last_request_time

                if elapsed_time < timedelta(minutes=minutes):
                    if request_count.count >= max_count:
                        return jsonify({"message": "Too many requests"}), 429
                    else:
                        request_count.count += 1
                else:
                    request_count.count = 1
                    request_count.last_request_time = datetime.now()
            else:
                # 如果数据库中没有记录，则创建新记录
                new_request_count = RequestCount(ip_address=ip_address, count=1, last_request_time=datetime.now(),api_name=interface_name)
                db.session.add(new_request_count)

            db.session.commit()

            return func(*args, **kwargs)

        return wrapper

    return decorator

#xiaojuzi v2
def _convert_to_pinyin(chinese):
    pinyin_list = pinyin(chinese, style=Style.NORMAL)
    pinyin_str = ''.join([item[0] for item in pinyin_list])
    return pinyin_str


#20231129 xiaojuzi v2 生成安全的API_KEY
def generate_api_key(length=32):
    characters = string.ascii_letters + string.digits
    api_key = ''.join(secrets.choice(characters) for _ in range(length))

    return api_key

#加密用户输入的账号密码  xiaojuzi v2 20231202
def hash_password(password):
    # 生成盐值
    salt = bcrypt.gensalt()
    # 哈希加密密码
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
    # 返回加密后的密码
    return hashed_password.decode('utf-8')

#检验用户输入的账号密码  xiaojuzi v2 20231202
def check_password(password, hashed_password):
    # 验证密码是否匹配
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

def make_device_qrcode(deviceid: str)->int:
    """
    生成设备二维码 格式 {"type":"share_device","device_id":"123456"} 对象转成base64，在用base64字符串生成二维码
    :param deviceid: 生成二维码字符串
    :return: errcode
    """
    try:
        str_info = '{"type":"share_device","device_id":"%s"}' % deviceid
        b64_byt = base64.b64encode(str_info.encode('utf-8'))
        b64_str = b64_byt.decode('utf-8')
        img = qrcode.make(b64_str)
        with open(os.path.join(os.path.abspath('.'), 'static', 'device', '%s.png' % deviceid), 'wb') as f:
            img.save(f)
    except Exception as e:
        logging.info(e)
        return SYSTEM_ERROR
    return SUCCESS


def cut_face_image(image_path, d_type=1):
    """
    检查并裁剪合适的人脸图片
    :param image_path: 图片地址
    :param d_type:     设备版本，1是第一代设备需要截取400X400像素 2是第二代设备保持原图片
    :return:
    """
    ft = FaceTool(image_path, d_type)
    if ft.crop_face():
        return ft.face_to_base64()
    else:
        return None


if __name__ == '__main__':
    # 调用函数并将生成的 API_KEY 存储在变量中
    api_key = generate_api_key()

    # 打印生成的 API_KEY
    print("Generated API_KEY:", api_key)

    # pinyin_str = _convert_to_pinyin('小光小光')
    # print(pinyin_str)
    # form_data = {
    #     'openid': 'oN3gn5OWMLVD1fmyRE4VThOMNzrc',
    #     # 'course_id': '3',
    #     # 'is_free': '1',
    #     'ts': str(int(time.time()))
    # }
    # st = '|'.join(['%s=%s' % (key, form_data[key]) for key in sorted(form_data)])
    # st = '%s|%s' % (st, SIGN_KEY)
    # form_data['tk'] = hashlib.md5(st.encode('utf8')).hexdigest()
    # print(form_data)
    # print(cut_face_image('d:\\Project\\PythonProject\\drawbo_project\\drawbo\\static\\face\\1660289997.png'))
