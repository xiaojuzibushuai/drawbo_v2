from sys_utils import db

#xiaojuzi
class User_Device(db.Model):

    __tablename__ = 'user_device'

    id = db.Column(db.Integer, primary_key=True)
    userid = db.Column(db.String(64),db.ForeignKey('user.openid'))
    deviceid = db.Column(db.String(32), db.ForeignKey('device.deviceid'))
    is_choose = db.Column(db.Boolean, default=True)   #设备是否选中 xiaojuzi

    sceneid = db.Column(db.Integer, db.ForeignKey('device_group.id'))

    #0为主动绑定 1为分享绑定
    status = db.Column(db.Integer, default=-1)

    #分享人
    shareby_userid = db.Column(db.String(64),default="")

    share_code = db.Column(db.String(20),default="")

    user = db.relationship('User', backref=db.backref('user_device'))

    device = db.relationship('Device', backref=db.backref('user_device'))

    device_group = db.relationship('DeviceGroup', backref=db.backref('user_device'))

    def __str__(self):
        return self.id