from sys_utils import db


class WxInfo(db.Model):
    """ 微信信息表 """
    __tablename__ = 'wx_info'
    id = db.Column(db.Integer, primary_key=True)
    jsapi_ticket = db.Column(db.String(255), default="")
    expires_in = db.Column(db.Integer, default=0)

    def __str__(self):
        return self.jsapi_ticket


class WxToken(db.Model):
    __tablename__ = 'wx_token'
    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(255), default="")
    expire_date = db.Column(db.Integer, default=0)

    def __str__(self):
        return self.token
