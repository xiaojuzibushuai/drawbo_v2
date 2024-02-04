from datetime import datetime

from sys_utils import db

#xiaojuzi 20231024
class UserExternalDevice(db.Model):

    __tablename__ = 'user_external_device'

    id = db.Column(db.Integer, primary_key=True)
    userid = db.Column(db.String(64), db.ForeignKey('user.openid'))

    # 画小宇设备id
    external_deviceid = db.Column(db.String(32), db.ForeignKey('device.deviceid'))

    # 外接设备id
    deviceid = db.Column(db.String(32), db.ForeignKey('external_device.deviceid'))

    # 绑定状态时间 20240202 xiaojuzi v2
    status_update = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    sceneid = db.Column(db.Integer, db.ForeignKey('device_group.id'))

    # 0为主动绑定 1为分享绑定
    status = db.Column(db.Integer, default=-1)

    #分享人
    shareby_userid = db.Column(db.String(64),default="")

    share_code = db.Column(db.String(20), default="")

    d_type = db.Column(db.Integer, default=3)  # 外设类型 0投影、摄像头 1导航机器人 2键盘 3其他

    is_choose = db.Column(db.Boolean, default=False)  # 设备是否选中 xiaojuzi


    user = db.relationship('User', backref=db.backref('user_external_device'))

    externaldevice = db.relationship('Device', backref=db.backref('user_external_device'))

    device = db.relationship('ExternalDevice', backref=db.backref('user_external_device'))

    device_group = db.relationship('DeviceGroup', backref=db.backref('user_external_device'))

    def __str__(self):
        return self.id