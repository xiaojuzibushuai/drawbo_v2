# mq_product 生产者
import json
import logging
import pika
from config import MQ_QUEUE_NAME, MQ_NAME, MQ_PASSWORD, MQ_HOST, MQ_PORT
from models.device import Device
from models.user import User
from models.user_device import User_Device
from utils.error_code import *


def send_message(push_dict: dict)->int:
    """
    查询openid对应的topic,并且发送数据到mq
    :param push_dict: dict
    :return: errcode
    本方法为v2版本 xiaojuzi  记录2023920
    """
    # 配置并连接
    user_info = pika.PlainCredentials(MQ_NAME, MQ_PASSWORD)  # 用户名和密码
    connection = pika.BlockingConnection(pika.ConnectionParameters(MQ_HOST, MQ_PORT, '/', user_info))  # 连接服务器上的RabbitMQ服务
    # 创建一个channel
    channel = connection.channel()
    # 如果指定的queue不存在，则会创建一个queue，如果已经存在 则不会做其他动作，官方推荐，每次使用时都可以加上这句
    channel.queue_declare(queue=MQ_QUEUE_NAME)

    openid = push_dict.get('fromuser', 'anonymity')

    deviceid = push_dict.get('deviceid', None)

    topic = 'iot/2/default_topic'
    status = None

    if openid == 'anonymity':
        topic = push_dict.get('topic')
        status = push_dict.pop('status')
    else:
        user = User.query.filter_by(openid=openid).first()
        if not user:
            return PARAMS_ERROR

        #修改地方 xiaojuzi
        if deviceid:
            device = User_Device.query.filter_by(userid=openid, deviceid=deviceid).first()
            if not device:
                return UNBIND_DEVICE

            # 获取该设备信息
            devices = Device.query.filter_by(deviceid=deviceid).first()

            # 取出topic和当前设备状态
            topic = devices.topic
            status = devices.status

    m_type = push_dict['type']
    logging.info('topic: %s, status: %s，m_type: %s, push_dict: %s' % (topic, status, m_type, push_dict.__str__()))
    push_dict['topic'] = topic
    push_body = str.encode(json.dumps(push_dict))

    # 判断设备状态，向可能状态的用户关联的所有设备发送订阅信息
    if m_type == 2 or m_type == 1:  # 音乐和课程需要检测是否闲状态
        if status == '128':  # 设备空闲
            pass
        elif status == '129':
            push_dict = {
                'topic': topic,
                'type': 3,
                'deviceid': deviceid,
                'fromuser': openid,
                'message': {'operate': 2}
            }
            push_body = str.encode(json.dumps(push_dict))
        elif status == '134':
            return DEVICE_CLOSE
        elif status == '144':
            return DEVICE_DOWNLOAD
        else:  # 否则返回h5提示
            return DEVICE_BUSY

    channel.basic_publish(
        exchange='',  # 当前是一个简单模式，所以这里设置为空字符串就可以了
        routing_key=MQ_QUEUE_NAME,  # 指定消息要发送到哪个queue
        body=push_body  # 指定要发送的消息
    )
    connection.close()
    return SUCCESS
