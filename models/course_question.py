from sys_utils import db
from datetime import datetime


class CourseQuestion(db.Model):
    """ 课程问题"""
    __tablename__ = 'course_question'

    id = db.Column(db.Integer, primary_key=True)

    question = db.Column(db.String(32), default="")
    questionkey = db.Column(db.Text, nullable=True)
    answer = db.Column(db.String(32), default="")
    answerkey = db.Column(db.String(32), default="")

    #问题排序
    question_order = db.Column(db.Integer,default=-1)

    #大游戏类别 20231121 xiaojuzi v2
    parentid = db.Column(db.Integer, db.ForeignKey('parent_game.id'))  # 大游戏id 20231121

    #课程id
    courseid = db.Column(db.Integer, db.ForeignKey('course.id'),default=-1)


    course = db.relationship('Course', backref=db.backref('course_question'))

