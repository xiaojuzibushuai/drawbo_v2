from sys_utils import db
from datetime import datetime



class DeviceCount(db.Model):
    """ 设备次数表"""
    __tablename__ = 'device_count'
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.Integer, nullable=False)
    use_count = db.Column(db.Integer, default=0)             # 使用次数

    def __str__(self):
        return self.id