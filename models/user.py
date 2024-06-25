from sys_utils import db
from datetime import datetime


class User(db.Model):
    """
    用户表--教师--家长
    """
    __tablename__ = 'user'
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

    role_id = db.Column(db.Integer, nullable=False, default=1)

    # 不使用 xiaojuzi
    device = db.Column(db.Integer, db.ForeignKey('device.id'))                       # 设备绑定
    device_info = db.relationship('Device', backref='user')

    def __str__(self):
        return self.openid


class FaceInfo(db.Model):
    """ 人脸管理表 """
    __tablename__ = 'face_info'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(32), default='')                                  # 设备人脸唯一id
    nickname = db.Column(db.String(20))
    sex = db.Column(db.SmallInteger, default=0, nullable=False)
    status = db.Column(db.SmallInteger, default=1, nullable=False)                  # 上课状态
    head = db.Column(db.String(512), default='')                                    # 头像
    feature = db.Column(db.Text, nullable=True)                                     # 人脸照片特征值
    img_base64 = db.Column(db.Text, nullable=True)                                  # 经过校验合法的人脸头像
    device = db.Column(db.Integer, db.ForeignKey('device.id'))                      # 设备
    uptime = db.Column(db.DateTime, default=datetime.now)
    phone = db.Column(db.String(15), default='')
    device_info = db.relationship('Device', backref='face_info')

    def __str__(self):
        return self.nickname


class CustomerService(db.Model):
    """ 客服管理 """
    __tablename__ = 'customer_service'
    id = db.Column(db.Integer, primary_key=True)
    phone = db.Column(db.String(15))                # 客服手机号
    active = db.Column(db.Boolean, default=True)    # 是否激活

    def __str__(self):
        return self.phone
