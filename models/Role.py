from sys_utils import db
from datetime import datetime


class Role(db.Model):
    """
    角色表
    """
    __tablename__ = 'role'
    id = db.Column(db.Integer, primary_key=True)

    role_name = db.Column(db.String(64))
    role_key = db.Column(db.String(64))
    status = db.Column(db.Integer, nullable=False, default=0)

    create_time = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    update_time = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)


    def __str__(self):
        return self.id