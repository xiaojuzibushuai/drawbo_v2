import redis
from flask_jwt_extended import JWTManager
from flask_sqlalchemy import SQLAlchemy
from flask import Flask
from flask_babelex import Babel


db = SQLAlchemy()
app = Flask(__name__, static_url_path='')
babel = Babel(app)
app.config.from_object('config')
db.init_app(app)




