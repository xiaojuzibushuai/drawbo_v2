import logging
import os
import re
import threading
import time
from datetime import datetime
import json

from flask import Blueprint

from sys_utils import db, app

import paho.mqtt.client as mqtt

from config import MQTT_USERNAME, MQTT_PASSWORD, MQTT_HOST, MQTT_PORT
from models.key_board_data import KeyBoardData
from models.mqtt_subscribe_message import mqttSubscribeMessage

import asyncio

#mqtt_sub 消费者服务器蓝图 20231028
mqtt_sub_api = Blueprint('mqtt_sub', __name__, url_prefix='/api/v2/mqtt_sub')

@app.before_first_request
#初始化实例化 20231028 xiaojuzi
def initialize():
    setup_mqtt()

# 创建锁对象 20231109 xiaojuzi 暂时解决办法
# lock = threading.Lock()
# 保存已处理的消息标识符
# processed_messages = set()

#xiaojuzi 20231027
def setup_mqtt():

    topic = "/keyboard/commit/"

    # 初始化MQTT
    client = mqtt.Client()
    client.username_pw_set(username=MQTT_USERNAME, password=MQTT_PASSWORD)

    # 订阅主题
    def on_connect(client, userdata, flags, rc):
        # 连接到 MQTT 服务器后的回调函数

        pid = os.getpid()

        # 订阅所需的主题
        client.subscribe(topic,1)

        logging.info( "MQTT消费者端pid为：" + str(pid) +"Connected to MQTT server with result code " + str(rc))
        # print("MQTT消费者端 Connected to MQTT server with result code " + str(rc))

    # MQTT回调函数，当接收到消息时调用 xiaojuzi 20231027
    def on_message(client, userdata, msg):

        # 检查消息标识符，避免处理重复的消息
        # if msg.mid in processed_messages:
        #     return None

        try:
            # 在应用上下文中执行插入数据的操作 updateby 20231117 xiaojuzi 修改逻辑
            with app.app_context():

                # 执行回调函数逻辑
                insert_mqmessage(msg)

                insert_data(msg)


        except Exception as e:
            # print('插入数据时出现异常:', str(e))
            logging.info('插入数据时出现异常:', str(e))

    # 设置连接和消息处理的回调函数
    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(MQTT_HOST, MQTT_PORT)

    client.loop_start()

    return client

def insert_mqmessage(msg):
    # 20231117 xiaojuzi v2 查询本地消息表该消息是否最近三十秒有数据 有就直接返回
    # query_param = msg.topic + '.' + msg.payload.decode()  有唯一索引就不需要这个

    s_message = db.session.query(mqttSubscribeMessage).filter_by(topic=msg.topic,payload=msg.payload.decode()).order_by(
        mqttSubscribeMessage.id.desc()).first()

    if s_message:
        if int(datetime.now().timestamp()) - s_message.status_update.timestamp() < 5:

            return None
        else:
            mqm = mqttSubscribeMessage(topic=msg.topic,
                                       payload=msg.payload.decode(),
                                       qos=msg.qos,
                                       status_update=datetime.now()
                                       )
            db.session.add(mqm)
            db.session.commit()
    else:
        mqm = mqttSubscribeMessage(topic=msg.topic,
                                   payload=msg.payload.decode(),
                                   qos=msg.qos,
                                   status_update=datetime.now()
                                   )
        db.session.add(mqm)
        db.session.commit()



# 数据插入函数 xiaojuzi 20231030
def insert_data(msg):
    # 解析JSON消息
    # message = json.loads(msg.payload.decode())
    # device = message['device']
    # title = message['title']
    # answer = message['answer']

    # 解析消息
    # {
    #   device:'小磊',
    #   title:'03',
    #   answer:'0'
    #   parentid:'1'
    #   }
    # 点号表示匹配除了换行符以外的任意字符 星号表示匹配前面的元素零次或多次 问号表示非贪婪匹配
    message = msg.payload.decode()

    device_match = re.search(r"device:'(.*?)'", message)
    title_match = re.search(r"title:'(.*?)'", message)
    answer_match = re.search(r"answer:'(.*?)'", message)
    parentid_match = re.search(r"parentid:'(.*?)'", message)

    if not device_match or not title_match or not answer_match or not parentid_match:
        return None

    device = device_match.group(1)

    title = title_match.group(1)

    answer = answer_match.group(1)

    parentid = parentid_match.group(1)

    #title为0 不统计
    if title == '0' or title == '00' or title == '' or title == ' ':
        return None

    data = db.session.query(KeyBoardData).filter_by(devicename=device, gametype=title, answer=answer,parentid=parentid).order_by(KeyBoardData.id.desc()).first()

    if data:
        #5s内不可重复作答
        if int(datetime.now().timestamp()) - data.status_update.timestamp() < 5:
            return None

        else:
            keyBoardData = KeyBoardData(devicename=device,
                                        gametype=title,
                                        answer=answer,
                                        parentid=parentid,
                                        status_update=datetime.now()
                                        )
            db.session.add(keyBoardData)
            db.session.commit()
    else:

        keyBoardData = KeyBoardData(devicename=device,
                                    gametype=title,
                                    answer=answer,
                                    parentid=parentid,
                                    status_update=datetime.now()
                                    )
        db.session.add(keyBoardData)
        db.session.commit()

    logging.info("insert key_board_data : %s", message)


