import redis
from flask import Blueprint
from flask_jwt_extended import JWTManager

from config import REDIS_HOST, REDIS_DB, REDIS_PORT
from sys_utils import app

auth_api = Blueprint('auth', __name__, url_prefix='/api/v2/auth')

# 创建 Redis 连接
jwt_redis_blocklist = redis.StrictRedis(
    host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True
)

# 在蓝图中初始化 JWTManager
jwt = JWTManager(app)

#令牌黑名单检查回调函数 xiaojuzi v2 20231204
@jwt.token_in_blocklist_loader
def check_if_token_in_blacklist(jwt_headers,jwt_payload):
    jti = jwt_payload['jti']
    token_in_redis = jwt_redis_blocklist.hget("jti",jti)
    # revoked_token = RevokedToken.query.filter_by(jti=jti).first()
    return token_in_redis is not None

