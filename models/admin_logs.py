from sys_utils import db
from datetime import datetime


class AdminLogs(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    scope = db.Column(db.String(120))
    username = db.Column(db.String(80))
    message = db.Column(db.String(255))
    ip = db.Column(db.String(60))
    uptime = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    def __str__(self):
        return self.id
