from sys_utils import db
from datetime import datetime


class Wakeword(db.Model):
    """ 设备唤醒词 """
    __tablename__ = 'wakeword'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), default=None)
    save_path = db.Column(db.String(64), default=None)     # 唤醒词地址

    def __str__(self):
        return self.name