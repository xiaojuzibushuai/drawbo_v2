import os
import logging
from datetime import timedelta

from sqlalchemy.pool import QueuePool

#Aky666666
# HOSTNAME = 'LOCALHOST'
# DATABASE = 'drawbo_db'
# DATABASE = 'drawbo_v2'
# USERNAME = 'root'
# PASSWORD = 'askroot'
# PASSWORD = '123456'

if os.getenv('drawbo'):
    # 正式环境
    logging.info('online config running')
    HOST = 'http://iot.v5ky.com'

    HOSTNAME = 'LOCALHOST'
    #线上
    # HOSTNAME = '121.89.199.156:31228'
    DATABASE = 'drawbo_v2'
    USERNAME = 'root'
    PASSWORD = 'askroot'
    # USERNAME = 'root'
    # PASSWORD = '123456'

    DEBUG = False

    # MYSQL
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://{}:{}@{}/{}'.format(
        USERNAME, PASSWORD, HOSTNAME, DATABASE
    )

    #设置最大连接数 xiaojuzi
    SQLALCHEMY_POOL_SIZE = 256

    SQLALCHEMY_POOL_RECYCLE = 3600

    #设置连接池实现类 20231109 xiaojuzi v2
    SQLALCHEMY_POOL_CLASS = QueuePool
    SQLALCHEMY_POOL_TIMEOUT = 60  # 连接超时时间为60秒
    SQLALCHEMY_POOL_OVERFLOW = 20 #最大溢出数20

    #设置数据库的SQL模式 xiaojuzi

    SQLALCHEMY_ENGINE_OPTIONS = {
        'connect_args': {
            'pool_recycle': 3600,  # 设置连接的回收时间为3600秒
            'sql_mode': 'STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION'}
    }
    SQLALCHEMY_TRACK_MODIFICATIONS = True


    ADMIN_HOST = 'http://101.201.75.83:8081'

else:
    # 测试环境
    HOST = 'http://172.16.0.230:5000'

    # HOSTNAME = 'LOCALHOST'
    # HOSTNAME = '121.89.199.156:31228'
    HOSTNAME = '101.201.75.83:3306'
    DATABASE = 'drawbo_v2'
    USERNAME = 'root'
    # PASSWORD = '123456'
    PASSWORD = 'askroot'

    DEBUG = True

    # logging.info('online config running')
    # HOST = 'http://101.201.75.83:3306'
    #
    # HOSTNAME = 'LOCALHOST'
    # DATABASE = 'drawbo_v2'
    # USERNAME = 'root'
    # PASSWORD = 'askroot'
    # DEBUG = False

    # MYSQL
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://{}:{}@{}/{}'.format(
        USERNAME, PASSWORD, HOSTNAME, DATABASE
    )

    SQLALCHEMY_POOL_SIZE = 256

    SQLALCHEMY_POOL_RECYCLE = 3600

    #设置连接池实现类 20231109 xiaojuzi v2
    SQLALCHEMY_POOL_CLASS = QueuePool
    SQLALCHEMY_POOL_TIMEOUT = 30  # 连接超时时间为30秒
    SQLALCHEMY_POOL_OVERFLOW = 20 #最大溢出数20

    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_recycle': 3600,  # 设置连接的回收时间为3600秒
        'connect_args': {'sql_mode': 'STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION'},
        # 'echo': True
    }

    SQLALCHEMY_TRACK_MODIFICATIONS = True

    ADMIN_HOST = 'http://101.201.75.83:8081'

    # # test2
    # logging.info('test2 config running')
    # # HOST = 'http://127.0.0.1:5555'
    # HOST = 'http://172.16.0.230:5000'
    # DEBUG = True
    # BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    # # SQLITE
    # SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(BASE_DIR, 'drawbo_db.sqlite')
    # SQLALCHEMY_TRACK_MODIFICATIONS = True

ALLOWED_EXTENSIONS = ['jpg', 'gif', 'png', 'jpeg']

BABEL_DEFAULT_LOCALE = 'zh_CN'
# set optional bootswatch theme
# FLASK_ADMIN_SWATCH = 'cerulean'

SECRET_KEY = "/\xb7\x99/1\x8e\x9b\xe4'oa'\xef\xe0\xb0u\x9bN_\xa8P\x86\xb1\xb1"

SIGN_KEY = 'sUpER2020KeY'

# miniprogram config
APPID = 'wx2f75d70111c3ec3d'
APPSECRET = '1053382b7b98527af3423663c778d62a'

# 短信配置
AccessKey_ID = 'LTAI5tQXBPYVNbuvvkmhdChh'
AccessKey_Secret = '6XpgesnInJvpQBWcEpKOpUXlWpQdF1'

SignName = '画小宇'
LoginTemplateCode = 'SMS_464040703'
ResetTemplateCode = 'SMS_464035626'
#请求短信验证接口的API_KEY
SMS_API_KEY = 'OK4QhEunXLN5wmMwyfNVmNQG6BzXMysu'
#短信过期时间
SMS_EXPIRE_TIME = 120
#设备在线判断时间
DEVICE_EXPIRE_TIME = 20

#定时任务配置 20240619 xiaojuz
SCHEDULER_API_ENABLED = True # 启用API端点，便于监控和管理
SCHEDULER_JOB_DEFAULTS = {
    'coalesce': False, # 防止相同作业的堆积执行
    'max_instances': 1,  # 限制同一作业同时运行的最大实例数
}

#认证授权配置 20231204 xiaojuzi timedelta(hours=1)
JWT_SECRET_KEY = 'FrZrkpM8Xwect1f2E1KfAB2bfEA9qYcE'
# JWT_HEADER_NAME = 'Authorization'
# JWT_HEADER_TYPE = 'Bearer'
JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=8)  #登录token过期时间
JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=15)  #刷新token过期时间

#Redis  k8集群 redis：121.89.199.156:31716
# REDIS_HOST = '101.201.75.83:6379'
REDIS_HOST = '121.89.199.156'
REDIS_PORT = 31716
# REDIS_PASSWORD = 'xiaojuziv2'
REDIS_DB = 0

#视频上传到OSS
oss_access_key_id = 'LTAI5tQEh2XoHCLNQV1zGUNt'
oss_access_key_secret = '905YkQEFw7kdiPLEv2clz6Xb7VrySG'
oss_endpoint = 'http://oss-cn-wuhan-lr.aliyuncs.com'
oss_bucket_name = 'kaiyu-video-resource'
cdn_oss_url = 'http://cdn.course.v5ky.com'

#加解密视频资源路径
video_resource_key = 'mKKXNLJFBoPzFFiPjMScMuUndgsfcxxwTF1VhkJEmX4='
#ffmpeg路径 线上使用
ffmpeg_path = '/var/www/ffmpeg/ffmpeg-6.1/ffmpeg'
ffprobe_path = '/var/www/ffmpeg/ffmpeg-6.1/ffprobe'

# 线上inkscape_path 地址：/var/www/squashfs-root/Inkscape.AppImage
# inkscape_path = 'E:/Inkscape/inkscape.exe'
inkscape_path = "E:/Inkscape1.1.2/bin/inkscape.exe"
# inkscape_path = '/var/www/squashfs-root/Inkscape.AppImage'


# RabbitMQ
MQ_HOST = '101.201.75.83'
MQ_PORT = 5672
MQ_NAME = 'drawbo'
MQ_PASSWORD = 'AsKdRaWbo2022'
MQ_QUEUE_NAME = 'drawbo'

# mqtt config 正式服务器 线上k8：121.89.199.156:31937 线上单机服务器：101.201.75.83:1883
MQTT_HOST = '121.89.199.156'
# MQTT_HOST = '172.16.0.230'
MQTT_PORT = 31937
MQTT_USERNAME = 'admin'
# MQTT_PASSWORD = 'public'
MQTT_PASSWORD = 'AsKdRaWbo20171117'
MQTT_CLIENT_ID = 'lens_27ArLs8BLsGQZu0Tt18eFtShBV5'

API_KEY = 'f369b7ec796c4dbd8d51'
