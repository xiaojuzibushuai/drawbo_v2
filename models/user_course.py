from sys_utils import db

#xiaojuzi 本表按需求设计形成用户和视频播放之间的关系 20240130
class User_Course(db.Model):

    __tablename__ = 'user_course'

    id = db.Column(db.Integer, primary_key=True)

    courseid = db.Column(db.String(32), db.ForeignKey('course.id'))

    phone = db.Column(db.String(15), default='')  # 手机号

    video_count = db.Column(db.Integer, default=0)  # 可用播放次数


    course = db.relationship('Course', backref=db.backref('user_course'))


    def __str__(self):
        return self.id