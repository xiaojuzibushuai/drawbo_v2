from sys_utils import db

#xiaojuzi 20231025


class DeviceGroup(db.Model):

    __tablename__ = 'device_group'

    id = db.Column(db.Integer, primary_key=True)

    # 分组名字
    groupname = db.Column(db.String(32), default="")

    #分组城市地点
    address = db.Column(db.String(32), default="")  # 城市

    def __str__(self):
        return self.id






