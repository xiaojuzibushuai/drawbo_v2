import json
import logging
from datetime import datetime

from api.auth import jwt_redis_blocklist
from config import MQTT_USERNAME, MQTT_PASSWORD, MQTT_HOST, MQTT_PORT, DEVICE_EXPIRE_TIME
from models.device import Device
from models.user import User, FaceInfo
from models.user_device import User_Device
from utils.error_code import *
import paho.mqtt.client as mqtt


def send_message(push_dict: dict)->int:
    """
    查询openid对应的topic,并且发送数据到mqtt
    :param push_dict: dict
    :return: errcode
    本方法为v2版本 xiaojuzi  记录2023920
    """
    openid = push_dict.get('fromuser', 'anonymity')

    deviceid = push_dict.get('deviceid', None)

    topic = 'iot/2/default_topic'
    status = None

    if openid == 'anonymity':
        topic = push_dict.get('topic')
        status = push_dict.pop('status')
    else:
        #
        # user = User.query.filter_by(openid=openid).first()
        # if not user:
        #     return PARAMS_ERROR
        #
        # #xiaojuzi 修改的地方
        # if deviceid:
        #     device = User_Device.query.filter_by(userid=openid,deviceid=deviceid).first()
        #     if not device:
        #         return UNBIND_DEVICE
        #
        #     #获取该设备信息
        #     devices = Device.query.filter_by(deviceid=deviceid).first()
        #
        #     # 取出topic和当前设备状态
        #     topic = devices.topic
        #     status = devices.status


        # 20240430 xiaojuzi 新逻辑实现
        topic = jwt_redis_blocklist.hget(f"iot_notify:{deviceid}","topic")
        status = jwt_redis_blocklist.hget(f"iot_notify:{deviceid}","updateStatus")

        #补偿机制
        if not topic or not status:
            #获取该设备信息
            devices = Device.query.filter_by(deviceid=deviceid).first()
            if not devices:
                return UNBIND_DEVICE
            # 取出topic和当前设备状态
            topic = devices.topic
            status = devices.status

    m_type = push_dict['type']
    logging.info('topic: %s, status: %s，m_type: %s, push_dict: %s' % (topic, status, m_type, push_dict.__str__()))
    push_dict['topic'] = topic
    # 判断设备状态，向可能状态的用户关联的所有设备发送订阅信息
    if m_type == 2 or m_type == 1:  # 音乐和课程需要检测是否闲状态
        if status == '128':  # 设备空闲
            pass
        elif status == '129': #设备播放时 20231026 xiaojuzi
            push_dict = {
                'topic': topic,
                'type': 3,
                'fromuser': openid,
                'deviceid': deviceid,
                'message': {
                    'operate': 2
                }
            }
        elif status == '134':
            return DEVICE_CLOSE
        elif status == '144':
            return DEVICE_DOWNLOAD
        else:  # 否则返回h5提示
            pass
            # return DEVICE_BUSY
    return send_message_to_topic(topic, push_dict)


#xiaojuzi  给外设设备发消息 自定义topic  20231030
def send_external_message(push_dict: dict,topic)->int:

    #以后等待扩展 TODO   20231030

    # 初始化MQTT
    push_body = str.encode(push_dict)
    client = mqtt.Client()
    client.username_pw_set(username=MQTT_USERNAME, password=MQTT_PASSWORD)
    client.connect(MQTT_HOST, MQTT_PORT)

    # 计划异步实现 xiaojuzi 20231023 qos=0 最多一次  1 最少一次 2 只有一次

    client.publish(topic, push_body, 1)
    logging.info("send_external_message_success: %s,topic: %s" % (push_body, topic))
    return SUCCESS

def send_message_to_topic(topic: str, push_dict: dict)->int:
    """
    :param topic:
    :param push_dict: 结构
    :return: errcode
    """
    push_body = str.encode(json.dumps(push_dict))
    # 初始化MQTT
    client = mqtt.Client()
    client.username_pw_set(username=MQTT_USERNAME, password=MQTT_PASSWORD)
    client.connect(MQTT_HOST, MQTT_PORT)

    #计划异步实现 xiaojuzi 20231023 qos=0 最多一次  1 最少一次 2 只有一次
    
    client.publish(topic, push_body, 1)

    logging.info("send_message_to_topic_success: %s,topic: %s" % (push_body, topic))

    return SUCCESS


def user_insert(face_id: int) -> int:
    """
    向设备发送添加用户请求
    :param face_id: face_id用来获取设备topic和状态
    :return: errcode
    """
    face_info = FaceInfo.query.get(face_id)
    deviceid = face_info.device_info.deviceid
    topic = face_info.device_info.topic

    #判断是否在线 在线则上传
    notify_time = jwt_redis_blocklist.hget(f"iot_notify:{deviceid}", "updateTime")
    if not notify_time:
        notify_time = 0

    if not (int(datetime.now().timestamp()) - int(notify_time) <= DEVICE_EXPIRE_TIME):
        return DEVICE_NOT_FIND

    push_dict = {
        "action": "user-insert",
        "header": {
            "reqid": deviceid  # 设备id
        },
        "body": {
            "users": [
                {
                    "userid": face_info.user_id,
                    # "data": face_info.img_base64
                }
            ]
        }
    }
    return send_message_to_topic(topic, push_dict)


def user_remove(face_id: int) -> int:
    """
    向设备发送删除用户请求
    :param face_id: face_id用来获取设备topic和状态
    :return: errcode
    """
    face_info = FaceInfo.query.get(face_id)
    deviceid = face_info.device_info.deviceid
    topic = face_info.device_info.topic

    #判断是否在线 在线则上传
    notify_time = jwt_redis_blocklist.hget(f"iot_notify:{deviceid}", "updateTime")
    if not notify_time:
        notify_time = 0

    if not (int(datetime.now().timestamp()) - int(notify_time) <= DEVICE_EXPIRE_TIME):
        return DEVICE_NOT_FIND

    push_dict = {
        "action": "user-remove",
        "header": {
            "reqid": deviceid  # 设备id
        },
        "body": {
            "users": [
                {
                    "userid": face_info.user_id,
                }
            ]
        }
    }
    return send_message_to_topic(topic, push_dict)
