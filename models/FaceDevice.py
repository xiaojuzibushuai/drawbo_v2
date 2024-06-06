from sys_utils import db
from datetime import datetime

class FaceDevice(db.Model):
    """人脸设备次数表"""
    __tablename__ = 'face_device'
    id = db.Column(db.Integer, primary_key=True)
    face_id = db.Column(db.Integer, nullable=False)
    device_id = db.Column(db.Integer, nullable=False)
    use_count = db.Column(db.Integer, default=0)             # 使用次数

    def __str__(self):
        return self.id