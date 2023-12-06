#!/usr/bin/env python
# -*-coding:utf-8 -*-
import random
import re
import string
import time

import requests
import json
from flask import request, jsonify, Blueprint
import logging
import os
from flask_jwt_extended import create_access_token, get_jwt_identity, create_refresh_token
from flask_jwt_extended import get_jwt
from flask_jwt_extended import jwt_required
from flask_jwt_extended import JWTManager

from sqlalchemy import func, cast, Integer, or_

from api.auth import jwt_redis_blocklist
from api.mqtt import mqtt_push_wakeword_data, mqttPushAnswerToKeyBoard, get_mqtt_push_volume, get_mqtt_push_direction
from config import HOST, APPSECRET, APPID, SignName, LoginTemplateCode, JWT_ACCESS_TOKEN_EXPIRES
from models.course_question import CourseQuestion
from models.device import Device
from models.logout_user import LogoutUser
from models.page import IndexAD, IndexRecommend, Share
from models.revoked_token import RevokedToken
from models.sms_send import SmsSend
from models.user import User, FaceInfo, CustomerService
from script.mosquitto_product import user_insert, user_remove
from sys_utils import db, app
from models.course import Category, CourseIntroduce, ContactUS, Course, DeviceCourse, DeviceCategory
from utils import sms_util
from utils.WXBizDataCrypt import WXBizDataCrypt
from utils.tools import ret_data, model_to_dict, dict_fill_url, dict_drop_field, decorator_sign, change_field_key, \
    dict_add_default_data, cut_face_image, create_noncestr, make_device_qrcode, rate_limit, require_api_key, \
    check_password, hash_password
from utils.error_code import *
from utils.districts import districts as region
from datetime import datetime, date

from models.user_device import User_Device
from models.user_external_device import UserExternalDevice
from models.external_device import ExternalDevice
from models.device_group import DeviceGroup
from Crypto.Cipher import AES

miniprogram_api = Blueprint('miniprogram', __name__, url_prefix='/api/v1')


@miniprogram_api.route('/test', methods=['GET', 'POST'])
# @jwt_required()
def test():
    current_user = get_jwt_identity()
    if not current_user:
        return jsonify(ret_data(UNAUTHORIZED_ACCESS))
    return jsonify({'message': 'Protected endpoint', 'user': current_user})


@miniprogram_api.route('/index', methods=['GET'])
def index():
    """
    首页
    :return: json
    """
    ad_list = IndexAD.query.filter(IndexAD.active == 1).all()
    recommend = db.session.query(
        IndexRecommend.id,
        IndexRecommend.course_id,
        IndexRecommend.priority,
        Course.img_files,
        Course.title
    ).join(Course, Course.id == IndexRecommend.course_id).filter(IndexRecommend.active == 1).all()
    position_ad = {}
    for ad in ad_list:
        if ad.position in position_ad:
            position_ad[ad.position].append(dict_fill_url(model_to_dict(ad), ['image']))
        else:
            position_ad[ad.position] = [dict_fill_url(model_to_dict(ad), ['image'])]
    data = {
        'recommend_course': dict_fill_url(model_to_dict(recommend), ['img_files']) if recommend else {},
        'ad': position_ad
    }
    return jsonify(ret_data(SUCCESS, data=data))


@miniprogram_api.route('/get_openid', methods=['GET'])
def get_openid():

    logging.info('get_openid api')
    code = request.args.get('code', None)
    if not code:
        return jsonify(ret_data(PARAMS_ERROR))
    logging.info('code is %s' % code)
    r = requests.get('https://api.weixin.qq.com/sns/jscode2session?appid=%s&secret=%s&js_code=%s&grant_type=authorization_code' % (APPID, APPSECRET, code))
    data = r.json()
    logging.info('data: %s' % r.content)

    if data.get('errcode', 0) == 0:
        # pop session_key
        data.pop('session_key')

        user = User.query.filter_by(openid=data['openid']).first()
        if not user:
            # 用户表创建记录
            user = User(openid=data['openid'])
            db.session.add(user)
            db.session.commit()
            logging.info('new user id:%s, openid:%s' % (user.id, data['openid']))

        return jsonify(data)

    return jsonify(data)

@miniprogram_api.route('/getUserDetailByWX', methods=['POST'])
#xiaojuzi v2 获取访问小程序用户的手机号 20231127
def getUserDetailByWX():

    logging.info('getUserDetailByWX api')

    code = request.form.get('code', None)

    if not code:
        return jsonify(ret_data(PARAMS_ERROR))

    # 优化 20231205 xiaojuzi v2
    r = requests.get(
        'https://api.weixin.qq.com/sns/jscode2session?appid=%s&secret=%s&js_code=%s&grant_type=authorization_code' % (
            APPID, APPSECRET, code))
    data = r.json()
    logging.info('data: %s' % r.content)
    try:
        if data.get('errcode', 0) == 0:

            # 提取 openid 和 session_key
            openid = data['openid']

            session_key = data['session_key']

            # 获取手机号
            encrypted_data = request.form.get('encryptedData')
            iv = request.form.get('iv')

            # 微信接口数据解密
            pc = WXBizDataCrypt(APPID, session_key)

            data_info = pc.decrypt(encrypted_data, iv)

            data_info['openid'] = openid

            data_info.pop('watermark')

            #执行注册方法 用户同意授权就默认注册 20231102 xioajuzi v2

            user = User.query.filter_by(register_phone=data_info['phoneNumber']).first()

            if user:
                user.uptime = datetime.now()
                db.session.commit()
            else:
                # 兼容v1版本的默认注册 xiaojuzi v2 20231129
                user1 = User.query.filter_by(openid=openid).first()
                if user1:
                    user1.uptime = datetime.now()
                    user1.register_phone = data_info['phoneNumber']
                    db.session.commit()
                else:
                    user2 = User(openid=openid,
                                 register_phone=data_info['phoneNumber'],
                                 uptime=datetime.now(),
                                 login_count=1
                                 )
                    db.session.add(user2)
                    db.session.commit()
                    logging.info('new user:%s' % (user2))

            logging.info('data_info:%s' % (data_info))

            return jsonify(ret_data(SUCCESS,data=data_info))

        return jsonify(ret_data(PARAMS_ERROR, data='getUserDetailByWX error！'))
    except Exception as e:
        logging.error('getUserDetailByWX error:%s' % e)
        return jsonify(ret_data(SUCCESS, data='getUserDetailByWX error'))

#用户账号密码登录接口  xiaojuzi v2 20231128
@miniprogram_api.route('/auth/loginByPassword', methods=['POST'])
# @decorator_sign
def loginByPassword():

    register_phone = request.form.get('register_phone', None)

    password = request.form.get('password', None)

    # if not validate_password(password):
    #     return jsonify(ret_data(PASSWORD_ERROR))

    if not validate_phone_number(register_phone):
        return jsonify(ret_data(PHONE_NUMBER_ERROR))

    user = User.query.filter_by(register_phone=register_phone).first()

    if not user :
        return jsonify(ret_data(PHONE_NOT_FIND))
    #校验密码 20231202 xiaojuzi v2
    is_valid = check_password(password, user.password)
    if is_valid:
        user.login_count += 1
        user.uptime = datetime.now()

        user1 = model_to_dict(user)

        db.session.commit()

        #生成令牌 20231204 xiaojuzi v2
        access_token = create_access_token(identity=user1)
        refresh_token = create_refresh_token(identity=user1)

        logging.info('user login:%s' % (user1))
        return jsonify(ret_data(SUCCESS, data={
            'message': '登录成功！',
            'access_token': access_token,
           'refresh_token': refresh_token,
        }))
    else:
        return jsonify(ret_data(PASSWORD_ERROR))


#用户手机号验证码登录注册一体接口 xiaojuzi v2 20231129
@miniprogram_api.route('/auth/register', methods=['POST'])
# @decorator_sign
def register():

    register_phone = request.form.get('register_phone', None)

    code = request.form.get('code', None)

    openid = request.form.get('openid', None)

    if not code or not openid:
        return jsonify(ret_data(PARAMS_ERROR))

    if not validate_phone_number(register_phone):
        return jsonify(ret_data(PHONE_NUMBER_ERROR))

    #判断验证码是否正确
    smsSend = SmsSend.query.filter_by(phone=register_phone).order_by(SmsSend.id.desc()).first()

    if not sendSms:
        return jsonify(ret_data(SMS_SEND_ERROR))

    if smsSend and (datetime.now() - smsSend.uptime).seconds < 120:
        if smsSend.code == code:

            user = User.query.filter_by(register_phone=register_phone).first()

            if user:

                user.login_count += 1
                user.uptime = datetime.now()

                user1 = model_to_dict(user)

                db.session.commit()

                # 生成令牌 20231204 xiaojuzi v2
                access_token = create_access_token(identity=user1)
                refresh_token = create_refresh_token(identity=user1)

                logging.info('user login:%s' % (user1))

                return jsonify(ret_data(SUCCESS, data={
                    'message': '登录成功！',
                    'access_token': access_token,
                   'refresh_token': refresh_token,
                }))
            else:
                #兼容v1版本的默认注册 xiaojuzi v2 20231129
                user1 = User.query.filter_by(openid=openid).first()
                if user1:
                    user1.login_count += 1
                    user1.uptime = datetime.now()
                    user1.register_phone = register_phone

                    user2 = model_to_dict(user1)
                    db.session.commit()

                    # 生成令牌 20231204 xiaojuzi v2
                    access_token = create_access_token(identity=user2)
                    refresh_token = create_refresh_token(identity=user2)

                    logging.info('user login:%s' % (user2))
                    return jsonify(ret_data(SUCCESS, data={
                        'message': '登录成功！',
                        'access_token': access_token,
                       'refresh_token': refresh_token,
                    }))
                else:
                    user2 = User(openid=openid,
                                 register_phone=register_phone,
                                 uptime=datetime.now(),
                                 login_count=1
                                 )
                    db.session.add(user2)
                    user3 = model_to_dict(user2)
                    db.session.commit()

                    # 生成令牌 20231204 xiaojuzi v2

                    access_token = create_access_token(identity=user3)
                    refresh_token = create_refresh_token(identity=user3)

                    logging.info('new user register_phone:%s, openid:%s' % (register_phone, openid))

                    return jsonify(ret_data(SUCCESS, data={
                        'message':'注册成功！',
                        'access_token': access_token,
                      'refresh_token': refresh_token,
                    }))
        else:
            return jsonify(ret_data(SMS_CODE_ERROR))
    else:
        return jsonify(ret_data(SMS_CODE_EXPIRE))

# 刷新令牌接口 xiaojuzi v2 20231204
@miniprogram_api.route('/auth/refreshToken', methods=['POST'])
@jwt_required(refresh=True)
def refreshToken():

    current_user = get_jwt_identity()
    if not current_user:
        return jsonify(ret_data(UNAUTHORIZED_ACCESS))
    # 生成新的访问令牌
    new_access_token = create_access_token(identity=current_user)
    return jsonify(ret_data(SUCCESS,data={'access_token': new_access_token}))

# 注销令牌接口（退出登录） xiaojuzi v2 20231204
@miniprogram_api.route('/auth/logout', methods=['DELETE'])
@jwt_required()
def logout():
    jti = get_jwt()['jti']
    ttype = get_jwt()["type"]
    # 将令牌加入黑名单
    jwt_redis_blocklist.hset("jti",jti, "")
    jwt_redis_blocklist.expire("jti", JWT_ACCESS_TOKEN_EXPIRES)
    return jsonify(ret_data(SUCCESS,data=f"{ttype.capitalize()} token successfully revoked"))

    # revoked_token = RevokedToken(jti=jti,created_at=datetime.now())
    # db.session.add(revoked_token)
    # db.session.commit()
    # return jsonify(ret_data(SUCCESS,data={'message': 'Successfully logged out'}))


#小程序用户个人中心重置密码接口  xiaojuzi v2 20231130
@miniprogram_api.route('/resetPassword', methods=['POST'])
# @jwt_required()
# @decorator_sign
def resetPassword():

    # current_user = get_jwt_identity()
    # if not current_user:
    #     return jsonify(ret_data(UNAUTHORIZED_ACCESS))

    logging.info('resetPassword api')

    register_phone = request.form.get('register_phone', None)

    code = request.form.get('code', None)

    password = request.form.get('password', None)

    if not validate_password(password):
        return jsonify(ret_data(PASSWORD_ERROR))

    if not validate_phone_number(register_phone):
        return jsonify(ret_data(PHONE_NUMBER_ERROR))

    if not code:
        return jsonify(ret_data(SMS_CODE_NOT_FIND))

    flage = check_sms_code(register_phone, code, 2)

    if flage:
        user = User.query.filter_by(register_phone=register_phone).first()
        #20231202 xiaojzi v2 加密密码
        hashed_password = hash_password(password)
        user.password = hashed_password
        db.session.commit()
        return jsonify(ret_data(SUCCESS))
    else:
        return jsonify(ret_data(RESET_PASSWORD_ERROR))

#更改用户个人信息接口  xiaojuzi v2 20231202
@miniprogram_api.route('/updateUserDetail', methods=['POST'])
@jwt_required()
def updateUserDetail():

    current_user = get_jwt_identity()
    if not current_user:
        return jsonify(ret_data(UNAUTHORIZED_ACCESS))

    logging.info('updateUserDetail api')

    openid = request.form.get('openid')

    user = User.query.filter_by(openid=openid).first()
    if not user:
        return jsonify(ret_data(USER_NOT_FIND))

    #更改信息 待完善

    db.session.commit()

    return jsonify(ret_data(SUCCESS,data='操作成功'))

#注销账号  xiaojuzi v2 20231205
@miniprogram_api.route('/cancelUserAccount', methods=['POST'])
@jwt_required()
def cancelUserAccount():

    current_user = get_jwt_identity()
    if not current_user:
        return jsonify(ret_data(UNAUTHORIZED_ACCESS))
    logging.info('cancelUserAccount api')

    openid = request.form.get('openid')
    phone = request.form.get('register_phone')

    user = User.query.filter(or_(User.openid==openid,User.register_phone==phone)).first()

    if user:
        logout_user = LogoutUser(openid=user.openid,register_phone=user.phone,
                                 password=user.password,nickname=user.nickname,
                                 sex=user.sex,true_name=user.true_name,
                                 phone=user.phone,address=user.address,
                                 login_count=user.login_count,
                                 ip=user.ip,uptime=user.uptime)

        db.session.add(logout_user)
        db.session.delete(user)
        db.session.commit()
        return jsonify(ret_data(SUCCESS,data='操作成功'))
    else:
        return jsonify(ret_data(CANCEL_USER_ACCOUNT_ERROR,data='操作失败'))


#小程序短信获取验证码接口  xiaojuzi v2 20231129
@miniprogram_api.route('/sendSms', methods=['POST'])
# @decorator_sign
@require_api_key
@rate_limit("/sendSms",10,10)
def sendSms():

    logging.info('sendSms api')

    register_phone = request.form.get('register_phone', None)

    if not validate_phone_number(register_phone):
        return jsonify(ret_data(PHONE_NUMBER_ERROR))

    #判断手机号当天是否发送次数超过10次 待修改
    check_count = check_sms_send_count(register_phone,10)

    if check_count:
        logging.info('sendSms api: phone:%s, check_count:%s' % (register_phone,check_count))
        return jsonify(ret_data(SMS_SEND_FREQUENTLY,data='操作失败'))

    #判断手机号2分钟内是否重复发送
    check_code = check_sms_send_code(register_phone,2)

    if check_code:
        logging.info('sendSms api: phone:%s, check_code:%s' % (register_phone,check_code))
        return jsonify(ret_data(SMS_SEND_FREQUENTLY,data='操作失败'))

    code = generate_verification_code()

    response = sms_util.send_sms(register_phone, SignName, LoginTemplateCode, code)

    if response['body']['Code'] != 'OK':
        return jsonify(ret_data(SMS_SEND_ERROR,data=response))
    else:
        smsSend1 = SmsSend(phone=register_phone, uptime=datetime.now(), send_count=1, code=code)
        db.session.add(smsSend1)
        db.session.commit()
        logging.info('sendSms api: phone:%s,code:%s response:%s' % (register_phone, code, response))

        return jsonify(ret_data(SUCCESS, data=response))


#xiaojuzi v2 20231130 判断验证码是否正确
def check_sms_code(phone,code,minute):

    smsSend = SmsSend.query.filter_by(phone=phone).order_by(SmsSend.id.desc()).first()

    if not smsSend:
        return False

    if smsSend and (datetime.now() - smsSend.uptime).seconds < (minute * 60):
        if smsSend.code == code:
            return True
        else:
            return False
    else:
        return False


#xiaojuzi v2 20231129 判断手机号是否某分钟内发送过短信
def check_sms_send_code(phone,minute):

    smsSend = SmsSend.query.filter_by(phone=phone).order_by(SmsSend.id.desc()).first()

    if not smsSend:
        return False

    if smsSend and (datetime.now() - smsSend.uptime).seconds < (minute * 60):
        return True
    else:
        return False


#xiaojuzi v2 20231129 判断手机号当天是否发送次数超限
def check_sms_send_count(phone,count):

    today_start_time = datetime.combine(date.today(), datetime.min.time())  # 当天的开始时间
    today_end_time = datetime.combine(date.today(), datetime.max.time())  # 当天的结束时间

    sms_count = SmsSend.query.filter(SmsSend.phone == phone,
                                     SmsSend.uptime >= today_start_time,
                                     SmsSend.uptime <= today_end_time).count()

    return sms_count > count


#xiaojuzi 验证码生成 v2 20231129
def generate_verification_code():

    characters = string.digits
    verification_code = ''.join(random.choice(characters) for _ in range(6))
    return verification_code

    # return str(random.randint(1000, 9999))


#xiaojuzi 密码复杂度校验 v2 20231128
def validate_password(password):
    # 密码长度至少为8个字符，包含至少一个大写字母、一个小写字母、一个数字和一个特殊字符
    # pattern = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!%*#?&]{8,}$'

    #密码长度至少为8个字符,至少包含一个字母、一个数字和一个特殊字符
    pattern = r'^(?=.*[a-zA-Z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!%*#?&]{8,}$'

    if re.match(pattern, password):
        return True
    else:
        return False


#xiaojuzi 手机号格式校验 v2 20231128
def validate_phone_number(phone_number):
    pattern = r'^(?:(?:\+|00)86)?1[3-9]\d{9}$'

    if re.match(pattern, phone_number):
        return True
    else:
        return False

@miniprogram_api.route('/multi_device_manage', methods=['POST'])
# @decorator_sign
@jwt_required()
#多设备用户绑定画小宇管理查询 xiaojuzi v2
def multi_device_manage():

    current_user = get_jwt_identity()
    if not current_user:
        return jsonify(ret_data(UNAUTHORIZED_ACCESS))

    openid = request.form.get('openid', None)

    #20231113 xiaojuzi v2 分组逻辑新增
    groupid = request.form.get('groupid', 1)

    user = User.query.filter_by(openid=openid).first()

    if not user or not groupid:
        return jsonify(ret_data(PARAMS_ERROR))

    #获取该用户的设备信息 分组逻辑新增 20231113 xiaojuzi
    devices = User_Device.query.filter_by(userid=openid,groupid=groupid)

    if not devices:
        return jsonify(ret_data(UNBIND_DEVICE))

    #判断设备是否在线
    device_data = []

    device_dict = {
        'id': '',
        'deviceid': '',
        'devicename': '',
        'apikey': '',
        'is_choose': '',
        'groupid': '',
        'is_master': '',
        'wakeword': '',
        'volume': '',
        'direction': '',
        'data': {
            'dev_online': '',
            'msg': ''
        }
    }

    for device in devices:

        device1 = Device.query.filter_by(deviceid=device.deviceid).first()

        device_dict['id'] = device1.id
        device_dict['deviceid'] = device1.deviceid
        device_dict['devicename'] = device1.devicename
        device_dict['is_choose'] = device.is_choose
        device_dict['groupid'] = device.groupid

        device_dict['apikey'] = device1.apikey
        device_dict['wakeword'] = device1.wakeword
        device_dict['is_master'] = device1.is_master
        device_dict['volume'] = device1.volume
        device_dict['direction'] = device1.direction

        if int(datetime.now().timestamp()) - device1.status_update.timestamp() <= 30:

            device_dict['data']['dev_online'] = True
            device_dict['data']['msg'] = '设备在线'

        else:

            device_dict['data']['dev_online'] = False
            device_dict['data']['msg'] = '设备离线'


        device_data.append(device_dict)

        device_dict = {
            'id': '',
            'deviceid': '',
            'devicename': '',
            'apikey': '',
            'is_choose': '',
            'groupid': '',
            'is_master': '',
            'wakeword': '',
            'volume': '',
            'direction': '',
            'data': {
                'dev_online': '',
                'msg': ''
            }
        }

    if not device_data:
        return jsonify(ret_data(UNBIND_DEVICE,data=None))
    else:
        return jsonify(ret_data(SUCCESS,data=device_data))


@miniprogram_api.route('/update_devicname', methods=['POST'])
@jwt_required()
# @decorator_sign
#多设备管理 设备名字修改 xiaojuzi v2
def update_devicname():

    current_user = get_jwt_identity()
    if not current_user:
        return jsonify(ret_data(UNAUTHORIZED_ACCESS))

    openid = request.form.get('openid', None)
    user = User.query.filter_by(openid=openid).first()

    deviceid = request.form.get('deviceid', None)
    devicename = request.form.get('devicename',None)

    if not user or not deviceid or not devicename:
        return jsonify(ret_data(PARAMS_ERROR))


    device = User_Device.query.filter_by(userid=openid,deviceid=deviceid).first()

    if device:
        device1 = Device.query.filter_by(deviceid=device.deviceid).first()

        device1.devicename = devicename
        db.session.commit()

        return jsonify(ret_data(SUCCESS, data='操作成功'))

    return jsonify(ret_data(UNBIND_DEVICE))

@miniprogram_api.route('/get_wakeword', methods=['GET'])
@jwt_required()
#多设备管理 设备唤醒词列表查询 xiaojuzi v2
def get_wakeword():

    current_user = get_jwt_identity()
    if not current_user:
        return jsonify(ret_data(UNAUTHORIZED_ACCESS))

    #前台需要嵌套数组
    data = [['小芳', '小花', '小凯','小丽','小智','小季','小爱','小黑','小磊','小美','小皮','小太','小妖','小源','小紫']]

    return jsonify(ret_data(SUCCESS, data=data))


@miniprogram_api.route('/getDevicebyId', methods=['GET'])
@jwt_required()
#设备管理获取设备详情信息 xiaojuzi v2 20231016
def getDevicebyId():

    current_user = get_jwt_identity()
    if not current_user:
        return jsonify(ret_data(UNAUTHORIZED_ACCESS))

    #获取url参数
    openid = request.args.get('openid', None)
    deviceid = request.args.get('deviceid',None)

    user = User.query.filter_by(openid=openid).first()
    if not user:
        return jsonify(ret_data(PARAMS_ERROR))

    device = User_Device.query.filter_by(userid=openid, deviceid=deviceid).first()

    if not device:
        return jsonify(ret_data(UNBIND_DEVICE))

    #进行设备详细信息查询
    device1 = Device.query.filter_by(deviceid=deviceid).first()

    device1 = model_to_dict(device1)

    device1 = change_field_key(device1, {'d_class': 'class'})
    device1 = change_field_key(device1, {'d_type': 'type'})


    return jsonify(ret_data(SUCCESS, data=device1))

@miniprogram_api.route('/updateDeviceById', methods=['POST'])
@jwt_required()
# @decorator_sign
#设备管理 设备详细信息修改 xiaojuzi v2 20231016
def updateDeviceById():

    current_user = get_jwt_identity()
    if not current_user:
        return jsonify(ret_data(UNAUTHORIZED_ACCESS))

    openid = request.form.get('openid', None)

    deviceid = request.form.get('deviceid', None)

    user = User.query.filter_by(openid=openid).first()
    if not user:
        return jsonify(ret_data(PARAMS_ERROR))

    device = User_Device.query.filter_by(userid=openid, deviceid=deviceid).first()
    if not device:
        return jsonify(ret_data(UNBIND_DEVICE))

    device1 = Device.query.filter_by(deviceid=deviceid).first()

    # 更新字段
    city = request.form.get('city', None)
    if city:
        device1.city = city
    school = request.form.get('school', None)
    if school:
        device1.school = school
    d_class = request.form.get('class', None)
    if d_class:
        device1.d_class = d_class
    phone = request.form.get('phone', None)
    if phone:
        device1.phone = phone
    if city or school or d_class or phone:
        db.session.commit()

    device1_info = model_to_dict(device1)

    device1_info = dict_drop_field(device1_info, ['apikey', 'productid', 'clientid', 'mac', 'remark', 'd_type', 'status',
                                                'create_at', 'topic', 'is_auth', 'qrcode_suffix_data', 'bind_type',
                                                'course', 'music_id', 'menu_id', 'status_update'])
    device1_info = change_field_key(device1_info, {'d_class': 'class'})

    return jsonify(ret_data(SUCCESS, data=device1_info))


@miniprogram_api.route('/update_wakeword', methods=['POST'])
@jwt_required()
# @decorator_sign
#多设备管理 设备唤醒词修改 xiaojuzi v2
def update_wakeword():

    current_user = get_jwt_identity()
    if not current_user:
        return jsonify(ret_data(UNAUTHORIZED_ACCESS))

    openid = request.form.get('openid', None)
    user = User.query.filter_by(openid=openid).first()

    deviceid = request.form.get('deviceid', None)
    wakeword = request.form.get('wakeword', None)

    if not user or not deviceid or not wakeword:
        return jsonify(ret_data(PARAMS_ERROR))

    device = User_Device.query.filter_by(userid=openid, deviceid=deviceid).first()
    device1 = Device.query.filter_by(deviceid=deviceid).first()

    if device:
        #在进一步行判断
        if (device.is_choose == True) & (int(datetime.now().timestamp()) - device1.status_update.timestamp() <= 30):

            device1.wakeword = wakeword

            result = mqtt_push_wakeword_data(openid,deviceid,wakeword)

            logging.info('硬件发送下载唤醒词数据接口 :%s' % result)

            db.session.commit()

            return jsonify(ret_data(SUCCESS, data='操作成功'))

        return jsonify(ret_data(SUCCESS, data="设备未选择或未在线"))

    return jsonify(ret_data(UNBIND_DEVICE))

@miniprogram_api.route('/choose_device_master', methods=['POST'])
@jwt_required()
# @decorator_sign
#多设备管理 设备是否选为主设备 xiaojuzi v2
def choose_device_master():

    current_user = get_jwt_identity()
    if not current_user:
        return jsonify(ret_data(UNAUTHORIZED_ACCESS))


    openid = request.form.get('openid', None)
    user = User.query.filter_by(openid=openid).first()
    if not user:
        return jsonify(ret_data(PARAMS_ERROR))

    deviceid = request.form.get('deviceid', None)

    #前端给出是否选中为主设备
    is_master = request.form.get('is_master', 0)

    device = User_Device.query.filter_by(userid=openid, deviceid=deviceid).first()

    if device:
        device1 = Device.query.filter_by(deviceid=device.deviceid).first()

        device1.is_master = is_master

        db.session.commit()

        return jsonify(ret_data(SUCCESS, data='操作成功'))

    return jsonify(ret_data(UNBIND_DEVICE))


@miniprogram_api.route('/device_switch', methods=['POST'])
@jwt_required()
# @decorator_sign
#选择设备循环联网 xiaojuzi v2 整体选择 包含全选 全不选
def device_switch():

    current_user = get_jwt_identity()
    if not current_user:
        return jsonify(ret_data(UNAUTHORIZED_ACCESS))

    deviceids = request.form.get('deviceids',None)
    openid = request.form.get('openid', None)
    deviceid_list = []
    if deviceids:
        #转数组
        deviceid_list = deviceids.split(",")
        #去重 可序列化
        deviceid_list = list(set(deviceid_list))

        user = User.query.filter_by(openid=openid)
        if not user:
            logging.info('openid:%s USER_NOT_FIND' % openid)
            return jsonify(ret_data(USER_NOT_FIND))

        for deviceid in deviceid_list:
            # 获取该用户的设备信息
            device = User_Device.query.filter_by(userid=openid,deviceid=deviceid).first()

            if not device:
                return jsonify(ret_data(DEVICE_NOT_FIND))

            device.is_choose = True

            db.session.commit()

            logging.info('用户（%s）更新device.id（%s）' % (openid, device.id))

    #将未选中的设备全改为未选中
    devices = User_Device.query.filter_by(userid=openid).all()

    for device in devices:
        if device.deviceid not in deviceid_list:

            device.is_choose = False
            db.session.commit()

    return jsonify(ret_data(SUCCESS,data=deviceid_list))

@miniprogram_api.route('/signle_device_switch', methods=['POST'])
@jwt_required()
# @decorator_sign
#选择单个设备循环联网 xiaojuzi v2   强调单个作用 非整体 接口 需求需要 20231114
def signle_device_switch():

    current_user = get_jwt_identity()
    if not current_user:
        return jsonify(ret_data(UNAUTHORIZED_ACCESS))

    deviceid = request.form.get('deviceid',None)
    openid = request.form.get('openid', None)
    user = User.query.filter_by(openid=openid).first()

    if not deviceid or not user:
        return jsonify(ret_data(PARAMS_ERROR))

    device = User_Device.query.filter_by(userid=openid,deviceid=deviceid).first()

    device.is_choose = not (device.is_choose)

    db.session.commit()

    return jsonify(ret_data(SUCCESS, data='修改成功'))

@miniprogram_api.route('/multipleUpdateDeviceVolume', methods=['POST'])
@jwt_required()
# @decorator_sign
#xiaojuzi v2   多设备批量调整音量 接口 需求需要 20231114
def multipleUpdateDeviceVolume():

    current_user = get_jwt_identity()
    if not current_user:
        return jsonify(ret_data(UNAUTHORIZED_ACCESS))

    openid = request.form.get('openid', None)
    deviceids = request.form.get('deviceids', None)
    volume = request.form.get('volume', None)

    if not openid or not deviceids or not volume:
        return jsonify(ret_data(PARAMS_ERROR))

    # 转数组
    deviceid_list = deviceids.split(",")
    # 去重 可序列化
    deviceid_list = list(set(deviceid_list))

    result = get_mqtt_push_volume(openid,deviceid_list,volume)

    logging.info('多设备批量调整音量接口 :%s' % result)

    if result == 0:
        return jsonify(ret_data(SUCCESS, data='操作成功'))

    return jsonify(ret_data(result, data='操作失败'))


@miniprogram_api.route('/multipleUpdateDeviceDirection', methods=['POST'])
@jwt_required()
# @decorator_sign
# xiaojuzi v2   多设备批量调整横竖版本 接口 需求需要 20231114
def multipleUpdateDeviceDirection():

    current_user = get_jwt_identity()
    if not current_user:
        return jsonify(ret_data(UNAUTHORIZED_ACCESS))

    openid = request.form.get('openid', None)
    deviceids = request.form.get('deviceids', None)

    #前端传需要变横版还是竖版的值
    direction = request.form.get('direction', None)

    if not openid or not deviceids or not direction:
        return jsonify(ret_data(PARAMS_ERROR))

    # 转数组
    deviceid_list = deviceids.split(",")
    # 去重 可序列化
    deviceid_list = list(set(deviceid_list))

    result = get_mqtt_push_direction(openid,deviceid_list,direction)
    logging.info('多设备批量调整绘画横版竖版接口 :%s' % result)

    if result == 0:
        return jsonify(ret_data(SUCCESS, data='操作成功'))

    return jsonify(ret_data(result, data='操作失败'))


@miniprogram_api.route('/device_unbind', methods=['POST'])
@jwt_required()
# @decorator_sign
#设备解绑 xiaojuzi v2
def device_unbind():

    current_user = get_jwt_identity()
    if not current_user:
        return jsonify(ret_data(UNAUTHORIZED_ACCESS))

    openid = request.form.get('openid', None)

    user = User.query.filter_by(openid=openid).first()

    if not user:
        return jsonify(ret_data(PARAMS_ERROR))

    deviceid = request.form.get('deviceid', None)

    device = User_Device.query.filter_by(userid=openid,deviceid=deviceid).first()
    if device:
        db.session.delete(device)
        db.session.commit()
        return jsonify(ret_data(SUCCESS,data='操作成功'))

    return jsonify(ret_data(UNBIND_DEVICE))


@miniprogram_api.route('/count_choose_online_device', methods=['POST'])
@jwt_required()
# @decorator_sign
#选中设备在线个数 xiaojuzi v2
def count_choose_online_device():

    current_user = get_jwt_identity()
    if not current_user:
        return jsonify(ret_data(UNAUTHORIZED_ACCESS))

    openid = request.form.get('openid', None)

    device_list = getDeviceByOpenid(openid)

    count = 0

    if device_list:
        count = len(device_list)

    return jsonify(ret_data(SUCCESS, data=count))


@miniprogram_api.route('/category', methods=['POST'])
def category():
    """
    获取课程类别  v2 xiaojuzi
    :return: json
    """
    openid = request.form.get('openid', None)

    #只要绑定设备默认所有设备的分类如果开启都可共享
    # 获取用户绑定选中且在线的设备
    device_list = getDeviceByOpenid(openid)

#     SELECT
#     category.id,
#     category.title,
#     category.detail,
#     category.save_path,
#     category.index_cate,
#     category.priority,
#     device_category.lock,
#     course.id AS free_course_id
#     FROM category
# LEFT JOIN device_category
# ON device_category.category_id = category.id
# LEFT JOIN course
# ON course.category_id = category.id
# WHERE category.index_cate = 1
# AND
# device_category.device_id in (
#     select id from device where deviceid in (
# select deviceid from user_device where userid = 'oN3gn5Dbdy9i6avagSpvymA473gQ'
# )
# )
# GROUP BY
# category.id

    if device_list:

        # 过滤条件
        query_deviceid = db.session.query(User_Device.deviceid).filter(User_Device.userid == openid)

        query_filter=[ Category.index_cate == 1]

        query_filter.append(Device.deviceid.in_(query_deviceid))

        course_query = (db.session.query(
                Category.id,
                Category.title,
                Category.detail,
                Category.save_path,
                Category.index_cate,
                Category.priority,
                DeviceCategory.lock,
                Course.id.label('free_course_id'),
            ).join(
                DeviceCategory,
                DeviceCategory.category_id == Category.id
            ).outerjoin(
                Course,
                Course.category_id == Category.id
            ).filter(*query_filter).group_by(Category.id,DeviceCategory.lock).all())

        # 进行相同id判断为true的留下
        ids = set()
        filtered_data = []

        #遍历获取数据id
        for item in course_query:
            ids.add(item[0])

        # 遍历只要分类开放的id
        for item in course_query:
            if item[0] in ids and not item[6]:
                filtered_data.append(item)
                ids.remove(item[0])

        if ids:
            #将未开放的id 加入
            for item in course_query:
                if item[0] in ids:
                    filtered_data.append(item)
                    ids.remove(item[0])
                    if not ids:
                        break

        #返回列表
        category_list = model_to_dict(filtered_data)

        category_list = dict_fill_url(category_list, ['save_path'])

    else:
        # 未绑定设备，也展示类别，但全部锁住
        cate_objs = db.session.query(
            Category.id,
            Category.title,
            Category.detail,
            Category.save_path,
            Category.index_cate,
            Category.priority,
            Course.id.label('free_course_id'),
        ).outerjoin(
            Course, Course.category_id == Category.id
        ).filter(Category.index_cate == 1).group_by(Category.id).all()

        category_list = model_to_dict(cate_objs)
        category_list = dict_fill_url(category_list, ['save_path'])

        for cate in category_list:
            cate['lock'] = True

    return jsonify(ret_data(SUCCESS, data=category_list))

    # 获取规整嵌套列表里面去外层列表 方式一
    # new_category_all_list = [category_list for innerlist in category_all_list for category_list in innerlist]
    #方式二 itertools.chain方法
    # new_category_all_list = list(itertools.chain(*category_all_list))


@miniprogram_api.route('/course', methods=['POST'])
@jwt_required()
# @decorator_sign
#    获取课程内容v2 xiaojuzi
def course():

    """
    获取课程内容v2 xiaojuzi
    request params: category_id（按课程分类）不填或等于0为获取所有课程
    :return: json
    """
    current_user = get_jwt_identity()
    if not current_user:
        return jsonify(ret_data(UNAUTHORIZED_ACCESS))

    openid = request.form.get('openid', None)
    course_id = request.form.get('course_id', None)
    category_id = request.form.get('category_id', None)
    course_class = request.form.get('course_class', None)
    volume = request.form.get('volume', None)

    if course_id == 'null':
        course_id = None

    # 获取用户绑定选中且在线的设备
    device_list = getDeviceByOpenid(openid)

    if not device_list:
        return jsonify(ret_data(DEVICE_NOT_FIND))

    #xiaojuzi
    # 创建查询参数
    # 课程查询字段
    #累加设备所查询到的课程使用次数
    query_params = [Course.id, Course.title, Course.detail, Course.category_id, Course.img_files,
                    Course.priority,Course.play_time, Course.course_class, Course.volume,
                    cast(func.sum(DeviceCourse.use_count),Integer).label('use_count'),Device.volume.label('sound_volume')]
    # 查询条件
    query_filter = [Course.index_show == 1]

    if category_id:
        query_filter.append(Course.category_id == int(category_id))

    if course_class:
        query_filter.append(Course.course_class == course_class)

    if volume:
        query_filter.append(Course.volume == volume)

    if course_id:
        query_filter.append(Course.id == int(course_id))

#     # 创建查询参数
#     query_params = [Course.title, func.sum(DeviceCourse.use_count)]
#
#     # 查询条件
#     query_filter = [Device.deviceid.in_(
#         db.session.query(User_Device.deviceid).filter(User_Device.userid == 'oN3gn5Dbdy9i6avagSpvymA473gQ'))]
#
#     # 进行关联查询
#     course_query = db.session.query(*query_params).join(
#         DeviceCourse, DeviceCourse.device_id == Device.id
#     ).join(
#         Course, Course.id == DeviceCourse.course_id
#     ).filter(*query_filter).group_by(Course.title)
#
#     # 执行查询
#     results = course_query.all()
#
#     # 处理查询结果
#     if results:
#         course_list = [{'title': title, 'use_count': use_count} for title, use_count in results]
#     else:
#         course_list = []

    # 过滤条件
    query_deviceid = db.session.query(User_Device.deviceid).filter(User_Device.userid == openid)

    query_filter.append(Device.deviceid.in_(query_deviceid))

    #执行sql
    course_query = db.session.query(*query_params).join(
        DeviceCourse, DeviceCourse.course_id == Course.id
    ).join(
            Device, Device.id == DeviceCourse.device_id
    ).filter(*query_filter).group_by(Course.title)

    course_objs = course_query.all()

    if course_objs:
        course_list = model_to_dict(course_query)
        course_list = dict_fill_url(course_list, ['img_files'])

        # 未绑定设置默认音量是0
        # if not device_id:
        #      course_list = dict_add_default_data(course_list, sound_volume=0)

    else:
        course_list = []

    return jsonify(ret_data(SUCCESS, data=course_list))


@miniprogram_api.route('/face_info', methods=['POST'])
@jwt_required()
# @decorator_sign
def face_info():
    """
    人脸信息/学生管理 v2 xiaojuzi
    :return: json
    """
    current_user = get_jwt_identity()
    if not current_user:
        return jsonify(ret_data(UNAUTHORIZED_ACCESS))

    openid = request.form.get('openid', None)
    face_id = request.form.get('face_id', None)
    update_data = request.form.get('update_data', None)
    # face_id,true;face_id,false;face_id,delete
    if update_data:
        try:
            logging.info(update_data)
            online_user = []                   # 需要下线的用户
            for fi in update_data.split(';'):
                face, status = fi.split(',')
                f = FaceInfo.query.get(face)
                if status == 'delete':
                    user_remove(f.id)
                    db.session.delete(f)
                else:
                    f.status = 1 if status == 'true' else 0
                    online_user.append(f.id)
                db.session.commit()
            if online_user:
                FaceInfo.query.filter(FaceInfo.id.notin_(online_user)).update({FaceInfo.status: 0}, synchronize_session='fetch')
                db.session.commit()
        except Exception as e:
            logging.info(e)
            return jsonify(ret_data(SYSTEM_ERROR))

    # 查询该设备学员信息
    #只要绑定设备默认所有设备的人脸都可共享
    face_all_list = []

    device_list = getDeviceByOpenid(openid)

    if not device_list:
        return jsonify(ret_data(DEVICE_NOT_FIND))

    for device in device_list:

        device_id = device.id

        if face_id:
            #根据 face_id 查询对应的人脸信息 xiaojujzi
            face = FaceInfo.query.get(int(face_id))

            data = []
            if face:

                data = model_to_dict(face)
                data = dict_fill_url(data, ['head'])
                data = dict_drop_field(data, ['img_base64', 'feature'])

                face_all_list.append(data)

            # else:
            #     return jsonify(ret_data(PARAMS_ERROR))

        else:

            #根据设备 ID 查询该设备关联的所有人脸信息 xiaojuzi
            face = FaceInfo.query.filter_by(device=device_id).all()

            data = []
            if face:
                data = model_to_dict(face)
                data = dict_fill_url(data, ['head'])
                data = dict_drop_field(data, ['img_base64', 'feature'])

                face_all_list.append(data)

    #去掉嵌套列表 xiaojuzi
    new_face_all_list = []

    for innerlist in face_all_list:
        if is_nested_list(innerlist):
            for face_list in innerlist:
                new_face_all_list.append(face_list)
        else:
            new_face_all_list.append(innerlist)

    # # 去重 用集合推导式 先转换为tuple 将tuple放入set集合 在转换为字典 不用去重 不同设备的人脸信息不一样
    # unique_new_face_all_list = [dict(t) for t in {tuple(sorted(d.items())) for d in new_face_all_list}]

    return jsonify(ret_data(SUCCESS, data=new_face_all_list))


@miniprogram_api.route('/create_face', methods=['POST'])
@jwt_required()
# @decorator_sign
def create_face():
    """ 人脸头像上传接口
        xiaojuzi v2 update by 2023922
     """

    current_user = get_jwt_identity()
    if not current_user:
        return jsonify(ret_data(UNAUTHORIZED_ACCESS))


    openid = request.form.get('openid', None)
    nickname = request.form.get('nickname', '')
    sex = request.form.get('sex', 0)
    sex = 0 if sex in ['男', '0', 0] else 1

    # 默认在一个机器上创建人脸 只上传一个人脸
    device_list = getDeviceByOpenid(openid)

    if not device_list:
        return jsonify(ret_data(DEVICE_NOT_FIND))

    for device in device_list:

        device_id = device.id

        # 上传图片
        f = request.files.get('upload')
        if not f:
            return jsonify(ret_data(PARAMS_ERROR))

        extension = f.filename.split('.')[1].lower()
        new_filename = str(int(time.time())) + '.' + extension

        if extension not in app.config['ALLOWED_EXTENSIONS']:
            return jsonify(ret_data(PARAMS_ERROR, data='只支持上传后缀为[jpg, gif, png, jpeg]的图片格式!'))
        image_path = os.path.join(os.path.abspath('.'), 'static', 'face', new_filename)

        f.save(image_path)
        # 检验图片是否有人脸
        cut_face_base64 = cut_face_image(image_path, device.d_type)

        if not cut_face_base64:
            return jsonify(ret_data(FACE_NOT_FIND))

        user_id = create_noncestr()

        face_obj = FaceInfo(
            user_id=user_id,
            nickname=nickname,
            sex=sex,
            device=device_id,
            head='face/' + new_filename,
            img_base64=cut_face_base64
        )

        db.session.add(face_obj)
        db.session.commit()

        logging.info('create deviceid(%s) , face(%s): nickname: %s, sex: %s, device: %s, head: %s ' % (device.deviceid,face_obj.id, nickname, sex, device_id, new_filename))

        data = model_to_dict(face_obj)
        data = dict_fill_url(data, ['head'])
        data = dict_drop_field(data, ['img_base64', 'feature'])

        # 发送mqtt信息到设备，获取feature值
        user_insert(face_obj.id)

        return jsonify(ret_data(SUCCESS, data=data))


@miniprogram_api.route('/update_face', methods=['POST'])
@jwt_required()
# @decorator_sign
def update_face():
    """ 人脸头像修改接口
        xiaojuzi v2 update by 2023922
    """
    current_user = get_jwt_identity()
    if not current_user:
        return jsonify(ret_data(UNAUTHORIZED_ACCESS))

    openid = request.form.get('openid', None)
    nickname = request.form.get('nickname', '')
    face_id = request.form.get('face_id', None)
    sex = request.form.get('sex', None)
    if sex is not None:
        sex = 0 if sex in ['男', '0', 0] else 1

    if not face_id:
        return jsonify(ret_data(PARAMS_ERROR))

    # xiaojuzi
    # 默认在一个机器上创建人脸 只上传一个人脸
    device_list = getDeviceByOpenid(openid)

    if not device_list:
        return jsonify(ret_data(DEVICE_NOT_FIND))

    for device in device_list:

        face_obj = FaceInfo.query.get(int(face_id))
        # 上传图片
        log_str = ''
        f = request.files.get('upload')
        if f:
            extension = f.filename.split('.')[1].lower()

            new_filename = str(int(time.time())) + '.' + extension

            if extension not in app.config['ALLOWED_EXTENSIONS']:
                return jsonify(ret_data(PARAMS_ERROR, data='只支持上传后缀为[jpg, gif, png, jpeg]的图片格式!'))

            image_path = os.path.join(os.path.abspath('.'), 'static', 'face', new_filename)

            f.save(image_path)

            # 检验图片是否有人脸
            cut_face_base64 = cut_face_image(image_path, device.d_type)

            if not cut_face_base64:
                return jsonify(ret_data(FACE_NOT_FIND))

            face_obj.head = 'face/' + new_filename
            face_obj.img_base64 = cut_face_base64
            log_str += 'head: %s' % new_filename

            # 发送mqtt信息到设备，获取feature值
            user_insert(face_obj.id)
        if nickname:
            face_obj.nickname = nickname
            log_str += 'nickname: %s' % nickname
        if sex is not None:
            face_obj.sex = sex
            log_str += 'sex: %s' % sex
        db.session.commit()

        logging.info('update by deviceid(%s) , face(%s): %s' % (device.deviceid,face_obj.id, log_str))

        data = model_to_dict(face_obj)
        data = dict_fill_url(data, ['head'])
        data = dict_drop_field(data, ['img_base64', 'feature'])

        return jsonify(ret_data(SUCCESS, data=data))

@miniprogram_api.route('/face_count_verify', methods=['POST'])
@jwt_required()
# @decorator_sign
def face_count_verify():
    """
    检测人脸数据是否符合，人数据超限，>20 则需暂停播放
     xiaojuzi v2 update by 2023922
    """

    current_user = get_jwt_identity()
    if not current_user:
        return jsonify(ret_data(UNAUTHORIZED_ACCESS))


    openid = request.form.get('openid', None)
    data = {'verify': True, 'content': ''}

    device_list = getDeviceByOpenid(openid)

    if not device_list:
        return jsonify(ret_data(DEVICE_NOT_FIND))

    for device in device_list:

        face_info_count = FaceInfo.query.filter_by(device=device.id, status=1).count()

        print(device.face_count, face_info_count)

        if device.face_count - face_info_count > 20:
            data = {'verify': False, 'content': '人数超限了，请确认'}
            # 弹过后将设备数量清0
            device.face_count = 0
            db.session.commit()

    return jsonify(ret_data(SUCCESS, data=data))


@miniprogram_api.route('/dev_online', methods=['POST'])
@jwt_required()
# @decorator_sign
def dev_online():
    """
    设备在线状态，实时 v2 xiaojuzi
    设备每秒上传一次设备状态
    接口随时调用，后台与设备上传的时间差值超过10秒钟，则显示“设备离线”，其它情况展示为“设备在线”
    :return: json
    """

    current_user = get_jwt_identity()
    if not current_user:
        return jsonify(ret_data(UNAUTHORIZED_ACCESS))


    openid = request.form.get('openid', None)
    user = User.query.filter_by(openid=openid).first()
    data = {'dev_online': False, 'msg': '设备离线'}

    if not user:
        data['msg'] = '未绑定设备'
        return jsonify(ret_data(SUCCESS, data=data))

    devices = User_Device.query.filter_by(userid=openid).all()

    if not devices:
        data['msg'] = '未绑定设备'
        return jsonify(ret_data(SUCCESS, data=data))

    for device in devices:

        device1 = Device.query.filter_by(deviceid=device.deviceid).first()

        if int(datetime.now().timestamp()) - device1.status_update.timestamp() <= 30:
            data['dev_online'] = True
            data['msg'] = '设备在线'

    return jsonify(ret_data(SUCCESS, data=data))


@miniprogram_api.route('/check_dev_bind', methods=['POST'])
@jwt_required()
# @decorator_sign
def check_dev_bind():
    """
    检查测试绑定状态
    v2 xiaojuzi
    """

    current_user = get_jwt_identity()
    if not current_user:
        return jsonify(ret_data(UNAUTHORIZED_ACCESS))


    openid = request.form.get('openid', None)
    user = User.query.filter_by(openid=openid).first()
    if not user:
        return jsonify(ret_data(PARAMS_ERROR))

    devices = User_Device.query.filter_by(userid=openid).all()

    if not devices:
        return jsonify(ret_data(UNBIND_DEVICE))

    data_list = []

    for device in devices:

        device1 = Device.query.filter_by(deviceid=device.deviceid).first()

        data = {'dev_bind': False,
                'deviceid': device1.deviceid
                }

        if device1.status:
            data = {'dev_bind': True,
                    'deviceid': device1.deviceid
                    }

        data_list.append(data)

    return jsonify(ret_data(SUCCESS, data=data_list))


#外接多设备绑定时查询用户绑定过的画小宇设备 20231024
@miniprogram_api.route('/getUserDeviceid', methods=['POST'])
@jwt_required()
# @decorator_sign
def getUserDeviceid():
    current_user = get_jwt_identity()
    if not current_user:
        return jsonify(ret_data(UNAUTHORIZED_ACCESS))
    #获取url参数
    # openid = request.args.get('openid', None)
    # deviceid = request.args.get('deviceid',None)

    #获取用户id
    openid = request.form.get('openid', None)

    user = User.query.filter_by(openid=openid).first()
    if not user:
        return jsonify(ret_data(PARAMS_ERROR))

    devices = User_Device.query.filter_by(userid=openid).all()

    if not devices:
        return jsonify(ret_data(UNBIND_DEVICE))

    device_data = []

    for device in devices:

        device1 = Device.query.filter_by(deviceid=device.deviceid).first()

        device1 = model_to_dict(device1)

        device_data.append(device1)

    return jsonify(ret_data(SUCCESS, data=device_data))


#外接多设备绑定 xiaojuzi v2 20231026
@miniprogram_api.route('/bindExternalDevice', methods=['POST'])
@jwt_required()
# @decorator_sign
def bindExternalDevice():
    current_user = get_jwt_identity()
    if not current_user:
        return jsonify(ret_data(UNAUTHORIZED_ACCESS))
    openid = request.form.get('openid', None)

    user = User.query.filter_by(openid=openid).first()
    if not user:
        return jsonify(ret_data(PARAMS_ERROR))

    deviceid = request.form.get('deviceid', None)

    device = ExternalDevice.query.filter_by(deviceid=deviceid).first()

    # 查询用户是否绑定画小宇设备 画小宇在第三方设备面前相当于外接设备

    external_deviceid = request.form.get('external_deviceid', None)
    external_device = Device.query.filter_by(deviceid=external_deviceid).first()

    if not (device or external_device):
        return jsonify(ret_data(UNBIND_DEVICE))

    if device.d_type != 3:
        #查询是否重复绑定 一个画小宇设备只允许绑定一个类型的外设设备
        user_external_device = UserExternalDevice.query.filter_by(
            userid=openid, external_deviceid=external_deviceid,d_type = device.d_type).first()

        if user_external_device:
            return jsonify(ret_data(REPEAT_BIND_DEVICE))

        #一个投影等外设设备只允许绑定一个画小宇设备20231108 xiaojuzi
        device1 = UserExternalDevice.query.filter_by(deviceid=deviceid).all()

        for de in device1:
            if de.external_deviceid:
                return jsonify(ret_data(REPEAT_BIND_DEVICE,data=f'已被画小宇设备号为:{de.external_deviceid}的绑定'))

        #进行绑定
        user_external_device1 = UserExternalDevice.query.filter_by(userid=openid, deviceid = deviceid).first()

        user_external_device1.external_deviceid = external_deviceid
        user_external_device1.d_type = device.d_type

        # userExternalDevice = UserExternalDevice(userid = openid,
        #                                         deviceid = deviceid,
        #                                         external_deviceid = external_deviceid,
        #                                         d_type=device.d_type
        #                                         )

        db.session.commit()

        return jsonify(ret_data(SUCCESS))

    else:
        user_external_device = UserExternalDevice.query.filter_by(
            userid=openid, external_deviceid=external_deviceid, deviceid = deviceid).first()

        if user_external_device:
            return jsonify(ret_data(REPEAT_BIND_DEVICE))

        # 进行绑定

        user_external_device1 = UserExternalDevice.query.filter_by(userid=openid, deviceid=deviceid).first()

        user_external_device1.external_deviceid = external_deviceid
        user_external_device1.d_type = device.d_type

        # userExternalDevice = UserExternalDevice(userid=openid,
        #                                         deviceid=deviceid,
        #                                         external_deviceid=external_deviceid,
        #                                         d_type=device.d_type
        #                                         )

        db.session.commit()

        return jsonify(ret_data(SUCCESS))


#外接多设备用户绑定外设查询 xiaojuzi v2 20231025
@miniprogram_api.route('/getBindExternalDevice', methods=['POST'])
@jwt_required()
# @decorator_sign
def getBindExternalDevice():
    current_user = get_jwt_identity()
    if not current_user:
        return jsonify(ret_data(UNAUTHORIZED_ACCESS))
    openid = request.form.get('openid', None)

    #20231113 xiaojuzi v2 分组逻辑新增
    groupid = request.form.get('groupid', 1)

    if not groupid:
        return jsonify(ret_data(PARAMS_ERROR))

    # 获取该用户绑定的外接设备信息 groupid 分组逻辑新增 20231113 xiaojuzi
    devices = UserExternalDevice.query.filter_by(userid=openid,groupid=groupid)

    if not devices:
        return jsonify(ret_data(UNBIND_DEVICE))

    device_data = []

    # 初始化
    device_dict = {
        'id': '',
        'deviceid': '',
        'devicename': '',
        'is_choose': '',
        'd_type': '',
        'mac': '',
        'groupid': '',
        'data': {
            'dev_online': '',
            'msg': ''
        }
    }

    for device in devices:

        device1 = ExternalDevice.query.filter_by(deviceid=device.deviceid).first()

        # 绑定过的外设设备信息则跳过20231025(去重 若deviceid唯一则不需要去重 预防测试数据扰乱) xiaojuzi
        device_ids = [device['deviceid'] for device in device_data]

        if device.deviceid in device_ids:
            continue

        device_dict['id'] = device1.id
        device_dict['deviceid'] = device1.deviceid
        device_dict['devicename'] = device1.devicename
        device_dict['d_type'] = device.d_type
        device_dict['mac'] = device1.mac

        device_dict['is_choose'] = device.is_choose
        device_dict['groupid'] = device.groupid

        device_dict['data']['msg'] = '设备存在'

        device_data.append(device_dict)

        # 初始化
        device_dict = {
            'id': '',
            'deviceid': '',
            'devicename': '',
            'is_choose': '',
            'd_type': '',
            'mac': '',
            'groupid': '',
            'data': {
                'dev_online': '',
                'msg': ''
            }
        }

    if not device_data:
        return jsonify(ret_data(UNBIND_DEVICE, data=None))
    else:
        return jsonify(ret_data(SUCCESS, data=device_data))

#外接多设备用户未绑定画小宇的外设查询 xiaojuzi v2 20231026
@miniprogram_api.route('/getUnbindExternalDevice', methods=['POST'])
@jwt_required()
# @decorator_sign
def getUnbindExternalDevice():
    current_user = get_jwt_identity()
    if not current_user:
        return jsonify(ret_data(UNAUTHORIZED_ACCESS))
    openid = request.form.get('openid', None)

    # 获取该用户绑定的外接设备信息
    devices = UserExternalDevice.query.filter_by(userid=openid)

    if not devices:
        return jsonify(ret_data(UNBIND_DEVICE))

    device_data = []

    # 初始化
    device_dict = {
        'id': '',
        'deviceid': '',
        'devicename': '',
        'is_choose': '',
        'd_type': '',
        'mac': '',
        'groupid': '',
        'data': {
            'dev_online': '',
            'msg': ''
        }
    }

    for device in devices:

        device1 = ExternalDevice.query.filter_by(deviceid=device.deviceid).first()

        # 绑定画小宇设备则跳过不显示20231026
        if device.external_deviceid:
            continue

        # 如果允许deviceid相同则加上type进行判断 预留
        # device_ids = [device['deviceid'] + '-' + device['d_type'] for device in device_data]
        #
        # check_deviceid = device.deviceid + '-' + device.d_type
        #
        # if check_deviceid in device_ids:
        #     continue

        # 绑定过的外设设备信息则跳过（去重 若deviceid唯一则不需要去重 预防测试数据扰乱） xiaojuzi
        device_ids = [device['deviceid'] for device in device_data]

        if device.deviceid in device_ids:
            continue

        device_dict['id'] = device1.id
        device_dict['deviceid'] = device1.deviceid
        device_dict['devicename'] = device1.devicename
        device_dict['d_type'] = device.d_type
        device_dict['mac'] = device1.mac

        device_dict['is_choose'] = device.is_choose
        device_dict['groupid'] = device.groupid

        device_dict['data']['msg'] = '设备存在'

        device_data.append(device_dict)

        # 初始化
        device_dict = {
            'id': '',
            'deviceid': '',
            'devicename': '',
            'is_choose': '',
            'd_type': '',
            'mac': '',
            'groupid': '',
            'data': {
                'dev_online': '',
                'msg': ''
            }
        }

    if not device_data:
        return jsonify(ret_data(UNBIND_DEVICE, data=None))
    else:
        return jsonify(ret_data(SUCCESS, data=device_data))


#外接多设备创建 xiaojuzi v2 20231024
@miniprogram_api.route('/createExternalDevice', methods=['POST'])
@jwt_required()
# @decorator_sign
def createExternalDevice():
    current_user = get_jwt_identity()
    if not current_user:
        return jsonify(ret_data(UNAUTHORIZED_ACCESS))
    openid = request.form.get('openid', None)

    user = User.query.filter_by(openid=openid).first()
    if not user:
        return jsonify(ret_data(PARAMS_ERROR))

    deviceid = request.form.get('deviceid', None)
    mac = request.form.get('mac', None)
    devicename = request.form.get('devicename',None)
    d_type = int(request.form.get('d_type',None))

    logging.info('d_type: %s,,devicename: %s, deviceid: %s, mac: %s' % (d_type,devicename, deviceid, mac))

    if not deviceid or not mac:
        return jsonify(ret_data(PARAMS_ERROR))

    device = ExternalDevice.query.filter_by(deviceid=deviceid).first()

    device1 = UserExternalDevice.query.filter_by(userid = openid,deviceid=deviceid).first()

    if not device:

        # 若没有设置名字则自动生成 xiaojuzi
        if not devicename:
            temp = 'AaBbCcDdEeFfGgHhIiJjKkLlMmNnOoPpQqRrSsTtUuVvWwXxYyZz1234567890'
            devicename = '画小宇外接设备'
            for i in range(5):
                devicename += random.choice(temp)

        #生成二维码
        make_device_qrcode(deviceid)

        de = ExternalDevice(
            deviceid=deviceid,
            mac=mac,
            devicename=devicename,
            d_type=d_type,
            qrcode_suffix_data='device/%s.png' % deviceid
        )

        db.session.add(de)

    if not device1:

        #用户新增默认绑定此外接设备
        de1 = UserExternalDevice(
            deviceid=deviceid,
            userid = openid,
            d_type=d_type
        )

        db.session.add(de1)

    #提交
    db.session.commit()

    return jsonify(ret_data(SUCCESS))

@miniprogram_api.route('/unbindExternalDevice', methods=['POST'])
@jwt_required()
# @decorator_sign
#外接设备解绑 xiaojuzi v2 20231025
def unbindExternalDevice():
    current_user = get_jwt_identity()
    if not current_user:
        return jsonify(ret_data(UNAUTHORIZED_ACCESS))
    openid = request.form.get('openid', None)

    user = User.query.filter_by(openid=openid).first()

    if not user:
        return jsonify(ret_data(PARAMS_ERROR))

    deviceid = request.form.get('deviceid', None)

    external_deviceid = request.form.get('external_deviceid', None)

    #如果external_deviceid没有接收到说明用户需要只与外设进行解绑 20231025
    if external_deviceid:
        device = UserExternalDevice.query.filter_by(userid=openid,deviceid=deviceid,external_deviceid=external_deviceid).first()
        if device:
            device.external_deviceid = None

            # db.session.delete(device)
            db.session.commit()
            return jsonify(ret_data(SUCCESS, data='操作成功'))

        return jsonify(ret_data(UNBIND_DEVICE))
    else:
        # 解绑外设自动将与外设绑定的画小宇设备也给删除
        devices = UserExternalDevice.query.filter_by(userid=openid, deviceid=deviceid).all()
        if devices:
            for device in devices:
                db.session.delete(device)
            db.session.commit()
            return jsonify(ret_data(SUCCESS, data='操作成功'))

        return jsonify(ret_data(UNBIND_DEVICE))


@miniprogram_api.route('/multiExternalDeviceManage', methods=['POST'])
@jwt_required()
# @decorator_sign
#用户绑定画小宇与其小伙伴管理 新模块界面所需查询 xiaojuzi v2 20231026
# 先查用户绑定的画小宇设备列表 用户与画小宇设备里放个集合保存用户外设与画小宇绑定的列表
def multiExternalDeviceManage():
    current_user = get_jwt_identity()
    if not current_user:
        return jsonify(ret_data(UNAUTHORIZED_ACCESS))
    openid = request.form.get('openid', None)
    user = User.query.filter_by(openid=openid).first()

    if not user:
        return jsonify(ret_data(PARAMS_ERROR))

    #获取该用户的设备信息
    devices = User_Device.query.filter_by(userid=openid)

    if not devices:
        return jsonify(ret_data(UNBIND_DEVICE))

    #判断设备
    device_data = []

    device_dict = {
        'id': '',
        'deviceid': '',
        'devicename': '',
        'apikey': '',
        'is_choose': '',
        'is_master': '',
        'wakeword': '',
        'volume': '',
        'data': {
            'dev_online': '',
            'device_external_data': ''
        }
    }

    for device in devices:

        device1 = Device.query.filter_by(deviceid=device.deviceid).first()

        # 获取用户绑定的外设设备信息 20231026
        device_external_data = getExternalDevice(openid,device.deviceid)

        device_dict['id'] = device1.id
        device_dict['deviceid'] = device1.deviceid
        device_dict['devicename'] = device1.devicename
        device_dict['is_choose'] = device.is_choose
        device_dict['apikey'] = device1.apikey
        device_dict['wakeword'] = device1.wakeword
        device_dict['is_master'] = device1.is_master
        device_dict['volume'] = device1.volume
        device_dict['data']['device_external_data'] = device_external_data

        if int(datetime.now().timestamp()) - device1.status_update.timestamp() <= 30:

            device_dict['data']['dev_online'] = True

        else:

            device_dict['data']['dev_online'] = False

        #添加进去
        device_data.append(device_dict)

        #初始化
        device_dict = {
            'id': '',
            'deviceid': '',
            'devicename': '',
            'apikey': '',
            'is_choose': '',
            'is_master': '',
            'wakeword': '',
            'volume': '',
            'data': {
                'dev_online': '',
                'device_external_data': ''
            }
        }

    if not device_data:
        return jsonify(ret_data(UNBIND_DEVICE,data=None))
    else:
        return jsonify(ret_data(SUCCESS,data=device_data))

#根据画小宇id openid查询 用户画小宇设备已经绑定的外设设备 xiaojuzi v2 20231027
@miniprogram_api.route('/getExternalDeviceBydeviceid', methods=['POST'])
@jwt_required()
# @decorator_sign
def getExternalDeviceBydeviceid():
    current_user = get_jwt_identity()
    if not current_user:
        return jsonify(ret_data(UNAUTHORIZED_ACCESS))
    openid = request.form.get('openid', None)
    user = User.query.filter_by(openid=openid).first()

    if not user:
        return jsonify(ret_data(PARAMS_ERROR))

    deviceid = request.form.get('deviceid', None)

    data = getExternalDevice(openid,deviceid)

    return jsonify(ret_data(SUCCESS,data=data))


#根据用户绑定的外设设备 键盘给相关外设设备进行答案下发 进行答案判别程序覆盖
# xiaojuzi 20231030
# @miniprogram_api.route('/pushAnswerToKeyBoard', methods=['POST'])
# @decorator_sign
# def pushAnswerToKeyBoard():
#
    # openid = request.form.get('openid', None)
    #
    # gametype = request.form.get('gametype', None)
    #
    # answer = request.form.get('answer', None)
#
#     user = User.query.filter_by(openid=openid).first()
#
#     if not user or not gametype or not answer:
#         return jsonify(ret_data(PARAMS_ERROR))
#
#     deviceid = request.form.get('deviceid', None)
#
#     data = getExternalDevice(openid,deviceid)
#
#     if data:
#         #选中用户绑定的键盘外设id发送此题答案
#         push_data = [d[deviceid] for d in data if(d['d_type'] == 2)]
#
#         mqttPushAnswerToKeyBoard(openid,push_data,gametype,answer)
#
#
#     return jsonify(ret_data(SUCCESS, data=data))


#对键盘群发题目信息 xiaojuzi 20231030
@miniprogram_api.route('/tempPushAnswerToKeyBoard', methods=['GET','POST'])
@jwt_required()
def tempPushAnswerToKeyBoard():
    current_user = get_jwt_identity()
    if not current_user:
        return jsonify(ret_data(UNAUTHORIZED_ACCESS))
    gametype = request.form.get('gametype', None)

    answer = request.form.get('answer', None)

    parentid = request.form.get('parentid', None)


    if not gametype or not answer or not parentid:
        return jsonify(ret_data(PARAMS_ERROR))

    #20231121 xiaojuzi v2
    mqttPushAnswerToKeyBoard(gametype, answer,parentid)

    return jsonify(ret_data(SUCCESS))


#根据课程id获取该课程的对应的问题和答案 xiaojuzi v2 20231106
@miniprogram_api.route('/getCourseQuestionData', methods=['POST'])
@jwt_required()
# @decorator_sign
def getCourseQuestionData():
    current_user = get_jwt_identity()
    if not current_user:
        return jsonify(ret_data(UNAUTHORIZED_ACCESS))
    openid = request.form.get('openid', None)
    user = User.query.filter_by(openid=openid).first()

    courseid = request.form.get('course_id', None)

    if not user or not courseid:
        return jsonify(ret_data(PARAMS_ERROR))

    question_data = []
    # 初始化 updateby xiaojuzi 20231122 v2 新增游戏类别
    question_dict = {
        'id': '',
        'question': '',
        'questionkey': '',
        'answer': '',
        'answerkey': '',
        'question_order': '',
        'parentid': ''
    }

    course_question = CourseQuestion.query.filter_by(courseid=courseid).all()

    if not course_question:
        return jsonify(ret_data(QUESTION_NULL))

    for question in course_question:

        question_dict['id'] = question.id
        question_dict['question'] = question.question
        question_dict['questionkey'] = question.questionkey
        question_dict['answer'] = question.answer
        question_dict['answerkey'] = question.answerkey
        question_dict['question_order'] = question.question_order
        question_dict['parentid'] = question.parentid

        question_data.append(question_dict)

        question_dict = {
            'id': '',
            'question': '',
            'questionkey': '',
            'answer': '',
            'answerkey': '',
            'question_order': '',
            'parentid': ''
        }

    if not question_data:
        return jsonify(ret_data(QUESTION_NULL,data=None))
    else:
        return jsonify(ret_data(SUCCESS,data=question_data))


#修改外设名字 xiaojuzi v2 20231107
@miniprogram_api.route('/updateExternalDevceName', methods=['POST'])
@jwt_required()
# @decorator_sign
def updateExternalDevceName():
    current_user = get_jwt_identity()
    if not current_user:
        return jsonify(ret_data(UNAUTHORIZED_ACCESS))
    openid = request.form.get('openid', None)

    user = User.query.filter_by(openid=openid).first()

    deviceid = request.form.get('deviceid', None)
    devicename = request.form.get('devicename',None)

    if not user or not deviceid or not devicename:
        return jsonify(ret_data(PARAMS_ERROR))

    device = UserExternalDevice.query.filter_by(userid=openid,deviceid=deviceid).first()

    if device:

        device1 = ExternalDevice.query.filter_by(deviceid=device.deviceid).first()

        device1.devicename = devicename
        db.session.commit()

        return jsonify(ret_data(SUCCESS, data='操作成功'))

    return jsonify(ret_data(UNBIND_DEVICE))


#查询个人注册详细信息 xiaojuzi v2 20231123  临时逻辑
@miniprogram_api.route('/getUserInfo', methods=['POST'])
@jwt_required()
# @decorator_sign
def getUserInfo():
    current_user = get_jwt_identity()
    if not current_user:
        return jsonify(ret_data(UNAUTHORIZED_ACCESS))
    userid = request.form.get('openid', None)

    user = User.query.filter_by(openid=userid).first()

    if not user:
        return jsonify(ret_data(PARAMS_ERROR))

    data = model_to_dict(user)

    return jsonify(ret_data(SUCCESS, data=data))


#查询分组信息 xiaojuzi v2 20231123  临时逻辑
@miniprogram_api.route('/getGroup', methods=['POST'])
@jwt_required()
# @decorator_sign
def getGroup():
    current_user = get_jwt_identity()
    if not current_user:
        return jsonify(ret_data(UNAUTHORIZED_ACCESS))
    group = DeviceGroup.query.all()

    group_data = []
    # 初始化
    group_dict = {
        'id': '',
        'groupname': '',
        'address': '',
    }

    for g in group:
        group_dict['id'] = g.id
        group_dict['groupname'] = g.groupname
        group_dict['address'] = g.address

        group_data.append(group_dict)

        group_dict = {
            'id': '',
            'groupname': '',
            'address': '',
        }

    return jsonify(ret_data(SUCCESS, data=group_data))


# 外接多设备与画小宇设备连接管理 获取用户画小宇设备绑定的外设列表 xiaojuzi v2 20231026
def getExternalDevice(openid: str,deviceid: str):

    # 获取该用户画小宇绑定的外接设备信息
    devices = UserExternalDevice.query.filter_by(userid=openid,external_deviceid=deviceid).all()

    if not devices:
        return None

    device_data = []
    # 初始化
    device_dict = {
        'id': '',
        'deviceid': '',
        'external_deviceid': '',
        'devicename': '',
        'is_choose': '',
        'd_type': '',
        'mac': '',
        'groupid': ''
        }

    for device in devices:

        device1 = ExternalDevice.query.filter_by(deviceid=device.deviceid).first()

        # 没有绑定画小宇设备则跳过不显示20231025
        # if not device.external_deviceid:
        #     continue

        device_dict['id'] = device1.id
        device_dict['deviceid'] = device1.deviceid
        device_dict['devicename'] = device1.devicename
        device_dict['mac'] = device1.mac

        device_dict['d_type'] = device.d_type
        device_dict['is_choose'] = device.is_choose
        device_dict['groupid'] = device.groupid
        device_dict['external_deviceid'] = device.external_deviceid


        device_data.append(device_dict)

        device_dict = {
            'id': '',
            'deviceid': '',
            'external_deviceid': '',
            'devicename': '',
            'is_choose': '',
            'd_type': '',
            'mac': '',
            'groupid': ''
        }

    if not device_data:
        return None
    else:
        return device_data


# 通过openid判断并获取到用户选择且在线的设备 xiaojuzi 2023923
def getDeviceByOpenid(openid: str) -> list:
    try:
        user = User.query.filter_by(openid=openid).first()

        if not user:
            return None

        # 查询用户已经绑定的设备id
        devices = User_Device.query.filter_by(userid=openid).all()

        if not devices:
            return None

        device_list = []

        for device in devices:
            device1 = Device.query.filter_by(deviceid=device.deviceid).first()
            if (device.is_choose == True) & (int(datetime.now().timestamp()) - device1.status_update.timestamp() <= 30):
                device_list.append(device1)

        return device_list

    except Exception as e:
        logging.info("发生了异常：%s" % str(e))
        return None

# 判断是否为嵌套列表 xiaojuzi 2023921
def is_nested_list(lst):
    if not isinstance(lst, list):
        return False

    return True


# @miniprogram_api.route('/unbind_device', methods=['POST'])
# @decorator_sign
def unbind_device():
    """
    解绑设备 此功能v2不使用 已丢弃 标注 2023923
    :return: json
    """
    openid = request.form.get('openid', None)
    user = User.query.filter_by(openid=openid).first()
    if not user:
        return jsonify(ret_data(PARAMS_ERROR))
    user.device = None
    db.session.commit()
    return jsonify(ret_data(SUCCESS))


@miniprogram_api.route('/share_device', methods=['POST'])
@jwt_required()
# @decorator_sign
def share_device():
    """
    分享设备  xiaojuzi 2023923
     暂定随机分享一个自己绑定的设备  此功能v2 版本用不用不不确定
    :return: json
    """
    current_user = get_jwt_identity()
    if not current_user:
        return jsonify(ret_data(UNAUTHORIZED_ACCESS))
    openid = request.form.get('openid', None)

    user = User.query.filter_by(openid=openid).first()
    if not user:
        return jsonify(ret_data(PARAMS_ERROR))

    user_device = User_Device.query.filter_by(userid=openid).all()

    if not user_device:
        return jsonify(ret_data(UNBIND_DEVICE))

    #暂定随机分享一个自己绑定的设备
    device = Device.query.filter_by(deviceid=random.choice(user_device.deviceid)).first()

    qrcode = HOST + '/' + device.qrcode_suffix_data

    return jsonify(ret_data(SUCCESS, data=qrcode))


@miniprogram_api.route('/link_bind/<deviceid>', methods=['POST'])
@jwt_required()
# @decorator_sign
def link_bind(deviceid):
    """
    通过分享链接绑定设备 v2 xiaojujzi 2023923
    :param deviceid: 采用设备ID串号进行绑定，防止伪造绑定其它设备
    :return: json
    """
    current_user = get_jwt_identity()
    if not current_user:
        return jsonify(ret_data(UNAUTHORIZED_ACCESS))
    openid = request.form.get('openid', None)

    user = User.query.filter_by(openid=openid).first()
    if not user:
        return jsonify(ret_data(PARAMS_ERROR))

    device = Device.query.filter_by(deviceid=deviceid).first()
    if not device:
        return jsonify(ret_data(DEVICE_NOT_FIND))

    user_device = User_Device.query.filter_by(userid=openid, deviceid=deviceid).first()

    if user_device:
        return jsonify(ret_data(REPEAT_BIND_DEVICE))

    user_device = User_Device(
        userid=openid,
        deviceid=deviceid
    )
    db.session.add(user_device)
    db.session.commit()

    return jsonify(ret_data(SUCCESS))


@miniprogram_api.route('/districts', methods=['GET'])
def districts():
    """
    区域
    :return: json
    """
    return jsonify(ret_data(SUCCESS, data=region))


@miniprogram_api.route('/get_class', methods=['GET'])
def get_class():
    """
    获取班级 暂定为 小班、中班、大班
    :return:
    """
    return jsonify(ret_data(SUCCESS, data=['小班', '中班', '大班']))


@miniprogram_api.route('/share', methods=['GET'])
def share():
    """
    小程序分享
    :return: json
    """
    s = Share.query.filter_by(isdel=0).first()
    return jsonify(ret_data(SUCCESS, data=dict_fill_url(model_to_dict(s), ['image_url'])))

@miniprogram_api.route('/course_introduce', methods=['GET'])
def course_introduce():
    """
    课程介绍
    :return: json
    """
    ci_objs = CourseIntroduce.query.filter_by(status=1).all()
    ci_list = model_to_dict(ci_objs)
    ci_list = dict_fill_url(ci_list, ['img_files', 'video_files'])
    return jsonify(ret_data(SUCCESS, data=ci_list))


@miniprogram_api.route('/contact_us', methods=['GET'])
def contact_us():
    """
    联系我们
    :return: json
    """
    c_us_objs = ContactUS.query.all()
    c_us_list = model_to_dict(c_us_objs)
    cs = CustomerService.query.filter_by(active=True).first()  # 取一个已激活的电话（暂定）
    result = {'content': c_us_list, 'phone': cs.phone}
    return jsonify(ret_data(SUCCESS, data=result))


# @miniprogram_api.route('/device_manage', methods=['POST'])
# @decorator_sign
def device_manage():
    """
    设备管理 v1版本使用 v2不使用 2023923 标注
    :return: json
    """
    openid = request.form.get('openid', None)
    user = User.query.filter_by(openid=openid).first()
    if not user:
        return jsonify(ret_data(PARAMS_ERROR))
    device = user.device_info
    if not device:
        return jsonify(ret_data(UNBIND_DEVICE))
    # 更新字段
    city = request.form.get('city', None)
    if city:
        device.city = city
    school = request.form.get('school', None)
    if school:
        device.school = school
    d_class = request.form.get('class', None)
    if d_class:
        device.d_class = d_class
    phone = request.form.get('phone', None)
    if phone:
        device.phone = phone
    if city or school or d_class or phone:
        db.session.commit()
    device = user.device_info
    device_info = model_to_dict(device)
    device_info = dict_drop_field(device_info, ['apikey', 'productid', 'clientid', 'mac', 'remark', 'd_type', 'status',
                                                'create_at', 'topic', 'is_auth', 'qrcode_suffix_data', 'bind_type',
                                                'course', 'music_id', 'menu_id', 'status_update'])
    device_info = change_field_key(device_info, {'d_class': 'class'})

    return jsonify(ret_data(SUCCESS, data=device_info))


@miniprogram_api.route('/reset_device', methods=['POST'])
@jwt_required()
# @decorator_sign
def reset_device():
    """
    恢复出厂设置
    :return: json
    """
    current_user = get_jwt_identity()
    if not current_user:
        return jsonify(ret_data(UNAUTHORIZED_ACCESS))
    return jsonify(ret_data(SUCCESS))