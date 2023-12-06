from datetime import datetime

from sys_utils import db

#xiaojuzi 20231117
class mqttSubscribeMessage(db.Model):

    __tablename__ = 'mqtt_subscribe_message'

    id = db.Column(db.Integer, primary_key=True)

    # query_param = db.Column(db.String(128), default="") #校验字段

    topic = db.Column(db.String(64), default="")  # 消息主题 xiaojuzi

    payload = db.Column(db.String(64), default="") #消息内容 xiaojuzi

    qos = db.Column(db.String(8), default="") #消息质量等级 xiaojuzi

    status_update = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)  # 消息接收时间


    def __str__(self):
        return self.id