from sys_utils import db
from datetime import datetime


class AuditUser(db.Model):
    """
    审核用户表 跟user表一样
    """
    __tablename__ = 'audit_user'
    id = db.Column(db.Integer, primary_key=True)
    register_phone = db.Column(db.String(15), default='')        # 注册手机号
    password = db.Column(db.String(15), default='')        # 用户密码 xiaojuzi updateby20231113
    avatar = db.Column(db.String(512), default='')              # xiaojuzi v2 头像

    nickname = db.Column(db.String(64))                             # 用户昵称
    openid = db.Column(db.String(64))                               # 微信openid
    sex = db.Column(db.SmallInteger, default=0)               # 性别
    true_name = db.Column(db.String(64))                            # 真实姓名
    phone = db.Column(db.String(15), default='')                                # 手机号
    address = db.Column(db.String(255))                             # 地址
    verification_code = db.Column(db.String(20))                    # 验证码
    code_expire_time = db.Column(db.Integer, default=0)             # 验证码发送时间过期
    login_count = db.Column(db.Integer, default=0)                  # 登录次数
    ip = db.Column(db.String(20))                                   # ip地址

    uptime = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now) #最近一次登录时间
    is_del = db.Column(db.Integer, nullable=False, default=0)       # 删除

    role_id = db.Column(db.Integer, nullable=False, default=2)


    def __str__(self):
        return self.openid