from sys_utils import db

#xiaojuzi 20231211
class DeviceGroup(db.Model):

    __tablename__ = 'device_group'

    id = db.Column(db.Integer, primary_key=True)

    userid = db.Column(db.String(64), db.ForeignKey('user.openid'))

    # 大场景
    scenename = db.Column(db.String(64), default="")

    # 小场景
    sub_scenename = db.Column(db.String(64), default="")

    # parentid = db.Column(db.Integer,default=-1)

    user = db.relationship('User', backref=db.backref('device_group'))


    def __str__(self):
        return self.id






