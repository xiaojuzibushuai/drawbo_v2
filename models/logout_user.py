from sys_utils import db
from datetime import datetime


class LogoutUser(db.Model):
    """
    注销的用户表
    """
    __tablename__ = 'logout_user'
    id = db.Column(db.Integer, primary_key=True)
    register_phone = db.Column(db.String(15), default=False)        # 注册手机号
    password = db.Column(db.String(15), default='123456')        # 用户密码 xiaojuzi updateby20231113
    avatar = db.Column(db.String(512), default='')              # xiaojuzi v2 头像

    nickname = db.Column(db.String(64))                             # 用户昵称
    openid = db.Column(db.String(64))                               # 微信openid
    sex = db.Column(db.SmallInteger, default=0)               # 性别
    true_name = db.Column(db.String(64))                            # 真实姓名
    phone = db.Column(db.String(15))                                # 手机号
    address = db.Column(db.String(255))                             # 地址
    login_count = db.Column(db.Integer, default=0)                  # 登录次数
    ip = db.Column(db.String(20))                                   # ip地址

    uptime = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now) #最近一次登录时间


    def __str__(self):
        return self.openid

