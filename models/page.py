from sys_utils import db
from datetime import datetime


class IndexAD(db.Model):
    """ 首页广告 """
    __tablename__ = 'index_ad'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(256), nullable=False)  # 标题
    image = db.Column(db.String(256), default="")  # 图片
    url = db.Column(db.String(256), default="")
    position = db.Column(db.String(256), default="")    # 位置
    active = db.Column(db.Boolean, default=True)
    priority = db.Column(db.Integer, default=999)  # 优先级
    uptime = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    def __str__(self):
        return self.title


class IndexRecommend(db.Model):
    """ 首页推荐 """
    __tablename__ = 'index_recommend'
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    active = db.Column(db.Boolean, default=True)
    priority = db.Column(db.Integer, default=999)  # 优先级
    course = db.relationship('Course', backref='index_recommend')
    uptime = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    def __str__(self):
        return self.id


class Share(db.Model):
    """ 分享 """
    __tablename__ = 'share'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128), nullable=False)           # 分享标题
    path = db.Column(db.String(128), nullable=False)            # 页面path，必须是以/开头的完整路径
    image_url = db.Column(db.String(256), nullable=False)       # 分享图标
    isdel = db.Column(db.Boolean, default=False, nullable=False)

    def __str__(self):
        return self.title
