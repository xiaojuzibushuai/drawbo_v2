import redis
from flask_jwt_extended import JWTManager
from flask_sqlalchemy import SQLAlchemy
from flask_apscheduler import APScheduler
from flask import Flask
from flask_babelex import Babel


db = SQLAlchemy()
scheduler = APScheduler()
app = Flask(__name__, static_url_path='')
babel = Babel(app)
app.config.from_object('config')
db.init_app(app)

# 设置为守护线程，默认情况下Flask-APScheduler应该已经是守护线程
scheduler.daemon = True
scheduler.init_app(app)



