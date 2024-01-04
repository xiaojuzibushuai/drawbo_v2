from datetime import datetime

from sys_utils import db

#xiaojuzi 20231211 暂时不使用

class Permission(db.Model):

    __tablename__ = 'share_permission'

    id = db.Column(db.Integer, primary_key=True)

    #分享设备id
    deviceid = db.Column(db.String(32),default="")

    # 权限级别 0 无权限 1 查看权限 2 控制权限 3 管理权限
    permission_level = db.Column(db.Integer, default=0)

    # 设备类型 1画小宇 2外设
    type = db.Column(db.Integer, default=0)

    userid = db.Column(db.String(64), default="")

    start_date = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)  # 开始时间

    end_date = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)  # 结束时间



    def __str__(self):
        return self.id






