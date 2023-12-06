from datetime import datetime
from sys_utils import db

class SmsSend(db.Model):
    """
    xiaojuzi v2 20231129
    短信发送记录
    """
    __tablename__ ='sms_send'

    id = db.Column(db.Integer, primary_key=True)

    phone = db.Column(db.String(15))                                # 手机号

    code = db.Column(db.String(20))                                # 验证码

    uptime = db.Column(db.DateTime, default=datetime.now)  #发送时间

    send_count = db.Column(db.Integer, default=0) # 发送次数