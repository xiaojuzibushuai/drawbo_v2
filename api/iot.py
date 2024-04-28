import json
import os
import random
import time

from flask import request, jsonify, Blueprint
import logging

from api.auth import jwt_redis_blocklist
from config import HOST, API_KEY
from models.course import DeviceCourse, Course, Category, DeviceCategory
from models.device import Device, QRCodeSerial
from models.user import User, FaceInfo
from models.user_device import User_Device
from script.mosquitto_product import send_message
from sys_utils import db
from utils.error_code import *
from utils.tools import iot_msg_manager, create_noncestr, ret_data, make_device_qrcode
from datetime import datetime, timedelta

iot_api = Blueprint('iot', __name__, url_prefix='/api/v1/iot')


@iot_api.route('/mqtt/iot_index', methods=['GET', 'POST'])
def iot_index():
    logging.info('test2 iot_index')
    if request.method == 'POST':
        re_method = 'POST'
    else:
        re_method = 'GET'
    return jsonify("iot_index", re_method)


@iot_api.route('/mqtt/image_data', methods=['GET', 'POST'])
def image_data():
    """
    获取人脸图片的base64编码
    :return:
    """
    logging.info('get image base64 data')
    userid = request.args.get('userid', None)
    if not userid:
        userid = request.json.get('userid', None)
    if not userid:
        return jsonify(iot_msg_manager(PARAMS_ERROR))
    face_info = FaceInfo.query.filter_by(user_id=userid).first()
    return jsonify(iot_msg_manager(SUCCESS, {
        'data': face_info.img_base64 if face_info else '',
        'name': face_info.nickname if face_info else ''
    }))


@iot_api.route('/mqtt/topic', methods=['POST'])
def iot_topic():
    """
    获取Topic&ClientID接口
    设备每次启动后，通过此接口向后台申请Topic & Clientid, 用于后面的MQTT消息通信。
    HTTP请求设置：
    Method: POST
    Content-Type: application/json
    Path: /iot/mqtt/topic
    :return: json
    """
    # # 用于接口请求授权验证 先注解掉
    # apikey = request.json.get('apikey', None)
    # # 设备唯一性标识
    # deviceid = request.json.get('deviceid', None)
    # custom = request.json.get('custom', 'custom')  # 配网时，此字段会发送
    # d_type = request.json.get('type', 0)           # 第二代主板，此字段为2，否则不上传 add by 20230708
    # logging.info('apikey: %s, deviceid: %s, custom: %s, d_type: %s' % (apikey, deviceid, custom, d_type))
    # payload = {}
    # clientid = create_noncestr()
    # payload['clientid'] = clientid
    # payload['topic'] = 'iot/2/1705395687'
    # logging.info("iot_clientid: %s",clientid)
    #
    #
    # return jsonify(iot_msg_manager(SUCCESS,payload))

    # 用于接口请求授权验证
    apikey = request.json.get('apikey', None)
    # 设备唯一性标识
    deviceid = request.json.get('deviceid', None)
    custom = request.json.get('custom', 'custom')  # 配网时，此字段会发送
    d_type = request.json.get('type', 0)           # 第二代主板，此字段为2，否则不上传 add by 20230708
    logging.info('apikey: %s, deviceid: %s, custom: %s' % (apikey, deviceid, custom))
    if not apikey or not deviceid:
        return jsonify(iot_msg_manager(PARAMS_ERROR))
    clientid = create_noncestr()
    payload = {}
    # 新写主题
    topic = "iot/2/%s" % deviceid + str(random.randint(0,100))
    # topic = 'iot/2/%s' % str(int(time.time()))
    device = Device.query.filter_by(deviceid=deviceid).first()

    if device:
        # 初始化课程及关系 20231109 修改 xiaojuzi 避免数据库人工插入数据造成系统条件判断缺失使用
        # init_course(device.id)
        # 生成二维码 20231202 xiaojuzi 修改 数据库人工插入数据造成系统条件判断缺失使用
        # make_device_qrcode(deviceid)
        #主题
        payload['topic'] = device.topic
        payload['clientid'] = device.clientid
    else:
        # 生成二维码
        make_device_qrcode(deviceid)
        # 新增一台设备
        device = Device(
            deviceid=deviceid,
            clientid=clientid,
            topic=topic,
            is_auth=1,
            d_type=int(d_type),
            qrcode_suffix_data='device/%s.png' % deviceid
        )
        db.session.add(device)
        db.session.commit()

        # 初始化课程及关系
        init_course(device.id)
        payload['topic'] = topic
        payload['clientid'] = clientid

    # # xiaojuzi v2版本
    if device.software_version == 'v2':

        # 若没有设置名字则自动生成 xiaojuzi
        if not device.devicename:
            temp = 'AaBbCcDdEeFfGgHhIiJjKkLlMmNnOoPpQqRrSsTtUuVvWwXxYyZz1234567890'
            devicename = '画小宇'
            for i in range(5):
                devicename += random.choice(temp)

            device.devicename = devicename
            db.session.commit()

        # 用户绑定设备 主动扫码（20231212 v2）
        user = User.query.filter_by(openid=custom).first()
        if user:
            # 新增用户设备信息表记录逻辑修改 xiaojuzi 20231214 v2 一个画小宇设备只允许一个人绑定 其他人绑定该设备只能分享添加
            device = User_Device.query.filter_by(deviceid=deviceid,status=0).first()
            # 待完善 20231218
            # device = User_Device.query.filter_by(userid=custom, deviceid=deviceid).first()
            if not device:

                user_device = User_Device(
                    deviceid=deviceid,
                    userid=custom,
                    status=0,
                    status_update=datetime.now()
                )
                db.session.add(user_device)
                db.session.commit()

            logging.info('user(%s) bind device(%s) success' % (custom, deviceid))
        else:
            logging.info(user)
        return jsonify(iot_msg_manager(SUCCESS, payload))

    # 原来的v1版本号 xiaojuzi
    else:
        # 用户绑定设备
        user = User.query.filter_by(openid=custom)

        if user:
            user.device = device.id
            db.session.commit()
            logging.info('user(%s) bind device(%s) success' % (custom, deviceid))
        else:
            logging.info(user)
    return jsonify(iot_msg_manager(SUCCESS, payload))


@iot_api.route('/status/notify', methods=['POST'])
def iot_notify():
    """
    状态报告接口
    用于设备端向后台上报设备的状态
    Method: POST
    Content-Type: application/json
    Path: /iot/status/notify
    :return: json
    """
    apikey = request.json.get('apikey', None)
    deviceid = request.json.get('deviceid', None)
    i_type = request.json.get('type', 0)
    status = request.json.get('status', None)
    if not apikey or not deviceid or not status:
        logging.info('状态上报参数不合法：apikey: %s, deviceid: %s, type: %s, status: %s' % (apikey, deviceid, i_type, status))
        return jsonify(iot_msg_manager(PARAMS_ERROR))

    #更新状态报告缓存
    count = jwt_redis_blocklist.get(f"iot_notify:{deviceid}")
    if count:
        newCount = jwt_redis_blocklist.incr(f"iot_notify:{deviceid}")
        jwt_redis_blocklist.set(f"iot_notify:{deviceid}", newCount, ex=timedelta(seconds=120))
        logging.info('更新缓存次数成功： deviceid: %s, type: %s, status: %s' % (deviceid, i_type, status))

        if newCount > 20:
            # 状态上报时间间隔大于20s，则更新设备表
            logging.info('更新数据库成功： deviceid: %s, type: %s, status: %s' % (deviceid, i_type, status))
            # # 更新设备表
            if i_type:
                Device.query.filter_by(deviceid=deviceid).update({
                    Device.status_update: datetime.now()
                })
                db.session.commit()

                #更新缓存
                jwt_redis_blocklist.set(f"iot_notify:{deviceid}", 1, ex=timedelta(seconds=120))

                return jsonify({'code': SUCCESS})
            else:
                # 只记录重要的状态变更日志
                # logging.info('apikey: %s, deviceid: %s, type: %s, status: %s' % (apikey, deviceid, i_type, status))
                Device.query.filter_by(deviceid=deviceid).update({
                    Device.d_type: i_type,
                    Device.status: status['devstatus']
                })
                db.session.commit()

                #更新缓存
                jwt_redis_blocklist.set(f"iot_notify:{deviceid}", 1, ex=timedelta(seconds=120))

                return jsonify(iot_msg_manager(SUCCESS))
    else:
        jwt_redis_blocklist.set(f"iot_notify:{deviceid}", 1, ex=timedelta(seconds=120))
        # jwt_redis_blocklist.expire("iot_notify",timedelta(days=7))

        logging.info('缓存成功： deviceid: %s, type: %s, status: %s' % (deviceid, i_type, status))

    return jsonify({'code': SUCCESS})

@iot_api.route('/message/send', methods=['POST'])
def iot_send():
    """
    消息发送接口
    用于设备端向后台发送各种类型消息
    Type=0: 语音对讲
    Type=1: 设备解绑
    Type=2: 选择科目
    Type=3: 设备绑定
    Type=4: 二维码课程
    Type=5: 二维码全球唯一ID
    Type=6: 上报人脸姓名
    Type=7: 上报课程
    Type=8: 上报特征值
    Type=9: 上报设备人数并且反馈人数是否超限
    HTTP请求设置：
    Method: POST
    Content-Type: application/json
    Path: /iot/message/send
    :return: json
    """
    apikey = request.json.get('apikey', None)
    i_type = request.json.get('type', 0)
    deviceid = request.json.get('deviceid', None)
    tousers = request.json.get('tousers', [])
    message = request.json.get('message', {})
    mediaid = request.json.get('mediaid', '')
    userkeys = request.json.get('userkeys', 0)
    logging.info('apikey:%s,type:%s,deviceid:%s,tousers:%s,message:%s,mediaid:%s,userkeys:%s' % (apikey, i_type, deviceid, tousers, message, mediaid, userkeys))
    if not apikey or not deviceid:
        return jsonify(iot_msg_manager(PARAMS_ERROR))
    """
    根据mediaid查找出所有的user里的openid，user和设备表是多对多的关系
    """
    if int(i_type) == 2:
        if 'userkeys' in message:  # 按键, 1:上一曲，2：下一曲， 18：设置键
            try:
                # 如果地址是空的，则使用mqtt发送mp3文件，http返回json{"code":0} update by wind 2019-01-05
                next_url = get_next_course(deviceid, message['userkeys'])
                if next_url == '':
                    return jsonify({'code': 0})
                url = next_url
            except Exception as e:
                logging.info(e)
                return jsonify(iot_msg_manager(SYSTEM_ERROR))
        else:
            # 修改为tf_card目录下的课程文件 update by wind 2019-01-17
            tf_card_url = os.path.join(HOST, 'static', 'tf_card', message['mediaid']).replace('\\', '/')
            logging.info('现在是插卡方式，发送tf卡的课程目录，url:{0}'.format(tf_card_url))
            url = tf_card_url
        return jsonify(iot_msg_manager(SUCCESS, {'url': url}))

    # 设备绑定 xiaojuzi
    if int(i_type) == 3:
        device = Device.query.filter_by(deviceid=deviceid).first()
        if not device:
            return jsonify(iot_msg_manager(DEVICE_NOT_FIND))
        openid = message['openid']
        user = User.query.filter_by(openid=openid)
        if not user:
            logging.info('openid:%s USER_NOT_FIND' % openid)
            return jsonify(iot_msg_manager(USER_NOT_FIND))
        logging.info('用户（%s）更新device.id（%s）' % (openid, device.id))

        # xiaojuzi 版本号判断 新版本执行
        if device.software_version == 'v2':

            # 若没有设置名字则自动生成 xiaojuzi
            if not device.devicename:
                temp = 'AaBbCcDdEeFfGgHhIiJjKkLlMmNnOoPpQqRrSsTtUuVvWwXxYyZz1234567890'
                devicename = '画小宇'
                for i in range(5):
                    devicename += random.choice(temp)

                device.devicename = devicename
                db.session.commit()

            # 新增用户设备信息表记录逻辑修改 xiaojuzi 20231214 v2 一个画小宇设备只允许一个人绑定 其他人绑定该设备只能分享添加
            device = User_Device.query.filter_by(deviceid=deviceid,status=0).first()
            #待完善 20231218
            # device = User_Device.query.filter_by(userid=openid, deviceid=deviceid).first()
            if not device:
                # 新增用户设备信息表记录 xiaojuzi
                user_device = User_Device(
                    deviceid=deviceid,
                    userid=openid,
                    status=0,
                    status_update=datetime.now()
                )
                db.session.add(user_device)
                db.session.commit()
        # v1 版本执行
        else:
            user.update({
                User.device: device.id
            })
            db.session.commit()

    # 二维码课程
    if int(i_type) == 4:
        course_name = message['lesson']
        course = Course.query.filter_by(title=course_name).first()
        if not course:
            return jsonify(iot_msg_manager(COURSE_NOT_FIND))
        url = os.path.join(HOST, 'static', 'upload', course.save_path, '%s_mc.mp3' % course.save_path).replace('\\', '/')
        return jsonify(iot_msg_manager(SUCCESS, {'url': url}))
    # 二维码全球唯一ID
    if int(i_type) == 5:
        uniqueid = message['uniqueid']
        qs = QRCodeSerial.query.filter_by(serial=uniqueid).first()
        if qs:
            return jsonify({'code': 1})
        else:
            qs = QRCodeSerial(serial=uniqueid)
            db.session.add(qs)
            db.session.commit()
            return jsonify({'code': 0})
    # 上报人脸姓名
    if int(i_type) == 6:
        name = message['name']
        logging.info('type:%s,name:%s' % (i_type, name))
        return jsonify(iot_msg_manager(SUCCESS, {'url': ''}))   # 欢迎小朋友音乐
    # 上报课程
    if int(i_type) == 7:
        course_name = message['name']
        course = Course.query.filter_by(title=course_name).first()
        if not course:
            return jsonify({'code': 0})
        url = os.path.join(HOST, 'static', 'upload', course.save_path).replace('\\', '/')
        return jsonify({'code': 1, 'payload': {'url': url}})
    # 上报特征值
    if int(i_type) == 8:
        user_id = message['userid']
        feature = message['feature']
        FaceInfo.query.filter_by(user_id=user_id).update({'feature': feature})
        db.session.commit()
    # 上报识别人数是否超数 暂时不检测人脸数量 xiaojuzi 2023923
    if int(i_type) == 9:
        device = Device.query.filter_by(deviceid=deviceid).first()
        if not device:
            return jsonify(iot_msg_manager(DEVICE_NOT_FIND))
        number = int(message['number'])  # 设备所识别的人数
        device.face_count = number
        db.session.commit()
        is_free = device.course_name
        face_info_count = FaceInfo.query.filter_by(device=device.id, status=1).count()
        logging.info('device face num: %d, service face num: %d' % (number, face_info_count))
        #修改免费课程不进行人脸数量检测  update by wind 20230328
        if is_free != 'free' and number - face_info_count > 20:
            logging.info('face too_many.mp3')
            return jsonify({'code': 1, 'payload': {'url': os.path.join(HOST, 'device', 'too_many.mp3')}})
    return jsonify(iot_msg_manager(SUCCESS))


@iot_api.route('/device/create', methods=['POST'])
def device_create():
    """
    新增设备
    apikey:     唯一值
    deviceid:   设备id,
    mac:        MAC地址
    :return: json
    """
    apikey = request.json.get('apikey', None)
    deviceid = request.json.get('deviceid', None)
    mac = request.json.get('mac', None)

    logging.info('apikey: %s, deviceid: %s, mac: %s' % (apikey, deviceid, mac))

    if not apikey or not deviceid or not mac:
        return jsonify(iot_msg_manager(PARAMS_ERROR))

    #20231118 xiaojuziv2 如果是mac地址带冒号那么替换一下
    # deviceid = deviceid.replace(":", "")

    # apikey先写死一个，以后可能会有扩展
    # topic = 'iot/2/%s' % deviceid+str(int(time.time()))  # 主题
    # 新写主题
    topic = "iot/2/%s" % deviceid + str(random.randint(0,100))
    clientid = create_noncestr()
    if apikey == API_KEY:
        device = Device.query.filter_by(deviceid=deviceid).first()

        # 初始化课程及关系 20231107 修改  xiaojuzi
        # init_course(device.id)

        if device:
            return jsonify(iot_msg_manager(DEVICE_EXIST))
        # 生成二维码
        make_device_qrcode(deviceid)
        de = Device(
            deviceid=deviceid,
            mac=mac,
            topic=topic,
            clientid=clientid,
            is_auth=1,
            qrcode_suffix_data='device/%s.png' % deviceid
        )
        db.session.add(de)
        db.session.commit()
        # 初始化课程及关系
        init_course(de.id)
        return jsonify(iot_msg_manager(SUCCESS))
    else:
        return jsonify(iot_msg_manager(APIKEY_NOT_EQUAL))


def get_next_course(deviceid, userkeys):
    """
    使用json数据，来定上下曲以及课程的选择 add by wind 2018-12-29
    :param deviceid: 设备id
    :param userkeys: 按键参数
    :return: http url
    """
    # 查询设备下是否有课程，如果没有课程，默认改为课程表第一项
    dev = Device.query.filter_by(deviceid=deviceid)
    base_dir = os.path.dirname(os.path.dirname(__file__))
    json_file_url = os.path.join(base_dir, 'static', 'upload', 'menu.json').replace('\\', '/')  # json文件地址
    base_url = os.path.join(HOST, 'static', 'upload').replace('\\', '/')
    if dev:
        device_obj = dev.first()
        logging.info('dev menu: %s' % device_obj.menu_id)
        logging.info('dev menu_course_pointer: %s' % device_obj.menu_course_pointer)
        logging.info('json file: %s' % json_file_url)
        f = open(json_file_url)
        menu_json = json.load(f)
        f.close()
        if int(userkeys) == 18:                      # 菜单键按下时，更新设备表id，mptt返回 '菜单.mp3'
            dev.update({                                                    # 更新菜单记录进设备
                Device.menu_id: (device_obj.menu_id + 1) % len(menu_json),
                Device.menu_course_pointer: -1
            })
            db.session.commit()
            arg = menu_json[device_obj.menu_id]['voice']
            menu_music = base_url + '/' + arg
            push_json = {
                'type': 1,
                'fromuser': 'anonymity',
                'message': {
                    'operate': 1,  # 0: stop 1: play 2: pause 4: resume
                    'arg': arg,
                    'url': menu_music,
                    'category': 0
                }
            }
            logging.info(push_json.__str__())
            topic = device_obj.topic
            status = device_obj.status
            logging.info('send menu mp3 topic: %s, status: %s' % (topic, status))
            push_json['topic'] = topic
            push_json['status'] = status
            errcode = send_message(push_json)
            logging.info('发送菜单音乐, %s' % ret_data(errcode).__str__())
            return ''                                               # 使用mqtt发送成功后，本接口需返回空路径

        elif int(userkeys) == 1:                                                            # 菜单键上一曲
            menu_course_list = menu_json[device_obj.menu_id]['course']                      # 课程列表
            up_pointer = (device_obj.menu_course_pointer - 1) % len(menu_course_list)       # 上一曲id
            dev.update({                                                                    # 更新菜单记录进设备
                Device.menu_course_pointer: up_pointer
            })
            db.session.commit()
            course_url = base_url + '/' + menu_course_list[up_pointer]
            return course_url
        else:                                                                               # 菜单键下一曲
            menu_course_list = menu_json[device_obj.menu_id]['course']                      # 课程列表
            down_pointer = (device_obj.menu_course_pointer + 1) % len(menu_course_list)     # 下一曲id
            dev.update({                                                                    # 更新菜单记录进设备
                Device.menu_course_pointer: down_pointer
            })
            db.session.commit()
            course_url = base_url + '/' + menu_course_list[down_pointer]
            return course_url
    else:
        raise IndexError

def init_course(device_id: int):
    """
    初始化与设备关联的课程和分类
    课程次数全设置为0
    分类为全锁
    :param device_id: 设备id
    :return: None
    """
    course_list = Course.query.all()
    for course in course_list:
        dc = DeviceCourse.query.filter_by(device_id=device_id, course_id=course.id).first()
        if not dc:
            device_course = DeviceCourse(
                course_id=course.id,
                device_id=device_id
            )
            db.session.add(device_course)
            db.session.commit()
    category_list = Category.query.all()
    for category in category_list:
        dc = DeviceCategory.query.filter_by(device_id=device_id, category_id=category.id).first()
        if not dc:
            device_category = DeviceCategory(
                category_id=category.id,
                device_id=device_id
            )
            db.session.add(device_category)
            db.session.commit()
