from sys_utils import db
from datetime import datetime


class CourseAudio(db.Model):
    """ 课程视频 JSON"""
    __tablename__ = 'course_audio'

    id = db.Column(db.Integer, primary_key=True)

    audiojson = db.Column(db.Text, default="")

    #课程id
    courseid = db.Column(db.Integer, db.ForeignKey('course.id'),default=-1)


