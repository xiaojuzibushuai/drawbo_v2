from datetime import datetime
from sys_utils import db

class RevokedToken(db.Model):
    """
    xiaojuzi v2 20231204
    过期的token 待考虑 先用redis
    """
    __tablename__ ='revoked_token'

    id = db.Column(db.Integer, primary_key=True)

    jti = db.Column(db.String(120))                                # token

    created_at = db.Column(db.DateTime, nullable=False)   #创建时间

