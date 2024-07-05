from datetime import datetime

from sys_utils import db

#xiaojuzi 20231027
class KeyBoardData(db.Model):

    __tablename__ = 'key_board_data'

    id = db.Column(db.Integer, primary_key=True)

    devicename = db.Column(db.String(32), default="")  # 设备名字 xiaojuzi

    deviceid = db.Column(db.String(32), default="")

    parentid = db.Column(db.Integer, db.ForeignKey('parent_game.id'))  # 大游戏id 20231120

    gametype = db.Column(db.String(8), default="") #游戏类型 xiaojuzi

    answer = db.Column(db.String(8), default="") #正确答案 xiaojuzi

    status_update = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)  # 更新状态时间

    # parent_game = db.relationship('ParentGame', backref=db.backref('parent_game'))


    def __str__(self):
        return self.id