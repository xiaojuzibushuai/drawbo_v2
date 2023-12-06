from datetime import datetime
from sys_utils import db

class RequestCount(db.Model):
    """
    xiaojuzi v2 20231129
    访问接口ip记录
    """
    __tablename__ ='requst_count'

    id = db.Column(db.Integer, primary_key=True)

    ip_address = db.Column(db.String(50))

    api_name = db.Column(db.String(50)) #接口名字

    last_request_time = db.Column(db.DateTime, default=datetime.now)  #最后一次访问时间

    count = db.Column(db.Integer, default=1)    #访问次数