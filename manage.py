from api.auth import auth_api
from api.subscribe_mqtt import mqtt_sub_api
from api.web_back import web_back_api
from sys_utils import app, db
import os
from logging.config import dictConfig
from flask_script import Manager, Command
from flask import redirect, url_for, request
from flask_migrate import Migrate, MigrateCommand
import logging
from flask_admin import Admin
from flask_security import Security, SQLAlchemyUserDatastore
from flask_ckeditor import upload_success, upload_fail
from flask_cors import CORS
# models
from models.admin_user import AdminUser, AdminRole
from models.admin_logs import AdminLogs
from models.user import User, FaceInfo, CustomerService
from models.wx_info import WxInfo
from models.device import Device, QRCodeSerial
from models.course import Course, Category, ContactUS, CourseIntroduce, DeviceCourse, DeviceCategory
from models.page import IndexAD, IndexRecommend, Share
# ----------- views start -----------
# 页面
from views.index_ad_view import IndexADView
from views.index_recommend_view import IndexRecommendView
# 用户
from views.user_view import UserView
from views.face_info_view import FaceInfoView
# 课程
from views.contact_us_view import ContactUsView
from views.category_view import CategoryView
from views.course_introduce_view import CourseIntroduceView
from views.course_view import CourseView
from views.device_category_view import DeviceCategoryView
from views.device_course_view import DeviceCourseView
# 设备
from views.device_view import DeviceView
from views.qrcode_serial_view import QRCodeSerialView
# 系统设置
from views.admin_index_view import CustomAdminIndexView
from views.share_view import ShareView
from views.admin_model_view import UserModelView, RoleModelView
from views.admin_logs_view import AdminLogsView
from views.customer_service_view import CustomerServiceView
# ----------- views end -----------
# api
from api.miniprogram import miniprogram_api
from api.mqtt import mqtt_api
from api.iot import iot_api

migrate = Migrate(app, db)
manager = Manager(app)
CORS(app)
# setup flask_security
user_data_store = SQLAlchemyUserDatastore(db, AdminUser, AdminRole)
security = Security(app, user_data_store)

class Run(Command):
    def run(self):
        #test2
        app.run(host='0.0.0.0',port=5000, debug=True)
        #线上
        # app.run(port=5555, debug=False)

manager.add_command('run', Run())
manager.add_command('db', MigrateCommand)

admin = Admin(app, name='管理后台', template_mode='bootstrap3', index_view=CustomAdminIndexView(name='起始页'),
              base_template='custom.html')

# add views
admin.add_views(
    # 页面设置
    IndexADView(IndexAD, db.session, name='首页广告', category='页面设置'),
    IndexRecommendView(IndexRecommend, db.session, name='首页推荐', category='页面设置'),
    # 课程管理
    CategoryView(Category, db.session, name='课程分类', category='课程管理'),
    CourseView(Course, db.session, name='课程内容', category='课程管理'),
    DeviceCategoryView(DeviceCategory, db.session, name='设备课程分类管理', category='课程管理'),
    DeviceCourseView(DeviceCourse, db.session, name='设备课程管理', category='课程管理'),
    CourseIntroduceView(CourseIntroduce, db.session, name='课程介绍', category='课程管理'),
    # 用户管理
    UserView(User, db.session, name='客户管理'),
    # 设备管理
    FaceInfoView(FaceInfo, db.session, name='人脸管理', category='设备管理'),
    DeviceView(Device, db.session, name='设备信息', category='设备管理'),
    QRCodeSerialView(QRCodeSerial, db.session, name='二维码管理', category='设备管理'),
    # 系统设置
    ContactUsView(ContactUS, db.session, name='联系我们', category='系统设置'),
    ShareView(Share, db.session, name='小程序分享设置', category='系统设置'),
    CustomerServiceView(CustomerService, db.session, name='客服管理', category='系统设置'),
    UserModelView(AdminUser, db.session, name='用户管理', category='系统设置'),
    RoleModelView(AdminRole, db.session, name='权限管理', category='系统设置'),
    AdminLogsView(AdminLogs, db.session, name='日志管理', category='系统设置'),
)


@app.route('/')
def hello_world():
    return redirect(url_for('admin.login_view'))


# 图片上传
@app.route('/image_upload', methods=['GET', 'POST'])
def image_upload():
    f = request.files.get('upload')
    extension = f.filename.split('.')[1].lower()
    if extension not in app.config['ALLOWED_EXTENSIONS']:
        return upload_fail(message='只支持上传后缀为[jpg, gif, png, jpeg]的图片格式!')
    f.save(os.path.join(os.path.abspath('.'), 'static', 'upload', f.filename))
    return upload_success(url='/upload_file/' + f.filename)                          # return upload_success call


# blueprint register
app.register_blueprint(auth_api)

app.register_blueprint(miniprogram_api)
app.register_blueprint(mqtt_api)
app.register_blueprint(iot_api)

app.register_blueprint(mqtt_sub_api)

app.register_blueprint(web_back_api)


# logger
def make_dir(make_dir_path):
    path = make_dir_path.strip()
    if not os.path.exists(path):
        os.makedirs(path)
    return path


log_dir_name = 'logs'
log_file_name = 'drawbo_log'
log_file_folder = os.path.abspath('.') + os.sep + log_dir_name
make_dir(log_file_folder)
log_file_str = log_file_folder + os.sep + log_file_name
log_level = logging.INFO

dictConfig({
    'version': 1,
    'formatters': {
        'default': {
            'format': '%(asctime)s [%(filename)s:%(funcName)s:%(lineno)d] [%(levelname)s] - %(message)s',
        }
    },
    'handlers': {
        'info_handler': {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': 'INFO',
            'formatter': 'default',
            'filename': log_file_str,
            'maxBytes': 1024*1024*20,  # 20 MB
            'backupCount': 50, #保留个数
            'encoding': 'utf8'
        }
    },
    'root': {
        'level': 'INFO',
        'handlers': ['info_handler']
    }
})

if __name__ == '__main__':
    manager.run()
