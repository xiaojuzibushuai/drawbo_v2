from datetime import datetime

from sys_utils import db

#xiaojuzi 20231120
class ParentGame(db.Model):

    __tablename__ = 'parent_game'

    id = db.Column(db.Integer, primary_key=True)

    game_name = db.Column(db.String(32), default="") #大游戏名字 xiaojuzi



    def __str__(self):
        return self.id