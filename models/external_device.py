from sys_utils import db
from datetime import datetime

#xiaojuzi 20231024
class ExternalDevice(db.Model):

    __tablename__ = 'external_device'

    id = db.Column(db.Integer, primary_key=True)
    deviceid = db.Column(db.String(32), default="")  # 设备id
    devicename = db.Column(db.String(32), default="")  # 设备名字 xiaojuzi
    mac = db.Column(db.String(16), default="")  # mac地址

    d_type = db.Column(db.Integer, default=3)  # 外设类型 0投影、摄像头 1导航机器人 2键盘 3其他

    qrcode_suffix_data = db.Column(db.Text, default="")                     # 设备二维码

    status_update = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)  # 更新状态时间


    def __str__(self):
        return self.id





