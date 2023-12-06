from datetime import datetime
from sys_utils import db


class Upload(db.Model):
    """ 上传的资源 """
    __tablename__ = 'upload'
    id = db.Column(db.Integer, primary_key=True)
    is_del = db.Column(db.Integer, default=0)
    owner = db.Column(db.Integer, default=0)
    file_path = db.Column(db.String(256), nullable=False)
    uptime = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    def __str__(self):
        return self.id
