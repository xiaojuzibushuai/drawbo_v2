from sys_utils import db
from datetime import datetime

class Goods(db.Model):

    """商品表"""
    __tablename__ = 'goods'

    id = db.Column(db.Integer, primary_key=True)
    good_image = db.Column(db.String(64))
    good_name = db.Column(db.String(64))
    good_info = db.Column(db.String(64))
    keyword = db.Column(db.String(64))
    cate_id = db.Column(db.String(64))
    price = db.Column(db.Integer,default=0)  # 分
    is_show = db.Column(db.Integer, nullable=False, default=1) # 0未上架 1上架
    create_time = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    update_time = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    goods_type = db.Column(db.String(64)) # 商品类型 # category-整套分类 course-单件课程
    out_business_id = db.Column(db.String(64))










