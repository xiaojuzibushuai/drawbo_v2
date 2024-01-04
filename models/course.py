from sys_utils import db
from datetime import datetime


class Course(db.Model):
    """ 课程 """
    __tablename__ = 'course'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(256), nullable=False)                                       # 标题
    detail = db.Column(db.String(256), default="")                                          # 详情
    save_path = db.Column(db.String(32), nullable=False)                                    # 上传课程目录名称
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)       # 种类
    voice_files = db.Column(db.Text, nullable=True)
    data_files = db.Column(db.Text, nullable=True)
    lrc_files = db.Column(db.Text, nullable=True)
    img_files = db.Column(db.Text, nullable=True)

    video_files = db.Column(db.Text, nullable=True) #20231227

    is_public = db.Column(db.Integer, default=1)
    love_number = db.Column(db.Integer, default=0)                                          # 喜爱度
    hard_number = db.Column(db.Integer, default=0)                                          # 难度
    index_show = db.Column(db.Integer, default=1, nullable=False)                           # 是否在首页显示
    uptime = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    priority = db.Column(db.Integer, default=999)                                           # 优先级，数字越小越靠前
    play_time = db.Column(db.Integer, default=240)                                          # 播放时间，默认240秒
    course_class = db.Column(db.String(16), default="小班", nullable=False)                 # 班级 （小班、中班、大班）
    volume = db.Column(db.String(16), default="上册", nullable=False)                       # 册别 （上册、下册）
    category = db.relationship('Category', backref='course')

    def __str__(self):
        return self.title


class Category(db.Model):
    """ 课程分类 """
    __tablename__ = 'category'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128), nullable=False)
    detail = db.Column(db.Text, nullable=True)                                              # 简介
    save_path = db.Column(db.String(64), default=None)                                      # 图片地址
    index_cate = db.Column(db.Integer, default=1, nullable=False)                           # 是否在首页展现种类
    priority = db.Column(db.Integer, default=999)                                           # 优先级，数字越小越靠前
    uptime = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    # course = db.relationship('Course', backref="category", lazy='dynamic')

    def __str__(self):
        return self.title


class CourseIntroduce(db.Model):
    """ 课程介绍 """
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128), default="")                                           # 标题
    content = db.Column(db.Text, default="")                                                # 内容
    img_files = db.Column(db.String(256), default="")                                       # 图片
    video_files = db.Column(db.String(256), default="")                                     # 视频
    status = db.Column(db.SmallInteger, default=1, nullable=False)                          # 是否有效
    priority = db.Column(db.Integer, default=999)                                           # 优先级
    tx_video_id = db.Column(db.String(256), default="")                                     # 腾讯视频id
    uptime = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    def __str__(self):
        return self.title


class ContactUS(db.Model):
    """ 联系我们 """
    __tablename__ = 'contactus'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128), default="", nullable=False)         # 标题
    content = db.Column(db.Text, default="", nullable=False)                  # 内容
    priority = db.Column(db.Integer, default=999)             # 优先级
    uptime = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    def __str__(self):
        return self.title


class DeviceCourse(db.Model):
    """ 设备课程管理 """
    __tablename__ = 'device_course'
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    device_id = db.Column(db.Integer, db.ForeignKey('device.id'), nullable=False)
    use_count = db.Column(db.Integer, default=0)             # 使用次数
    course = db.relationship('Course', backref='device_course')
    device = db.relationship('Device', backref='device_course')

    def __str__(self):
        return self.id


class DeviceCategory(db.Model):
    """ 设备分类管理 """
    __tablename__ = 'device_category'
    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    device_id = db.Column(db.Integer, db.ForeignKey('device.id'), nullable=False)
    lock = db.Column(db.Boolean, default=True)                         # 是否锁住
    category = db.relationship('Category', backref='device_category')
    device = db.relationship('Device', backref='device_category')

    def __str__(self):
        return self.id
