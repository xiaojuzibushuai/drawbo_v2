import base64
import json
import os
import time
from datetime import datetime

import oss2
import redis
import logging
from flask import request, jsonify, Blueprint
from flask_jwt_extended import JWTManager, create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from sqlalchemy import func, cast, Integer

from api.miniprogram import validate_phone_number, generate_nickname, sendSms, validate_password, getDeviceByOpenid
from api.mqtt import sortDeviceByMaster
from config import REDIS_HOST, REDIS_DB, REDIS_PORT, oss_access_key_id, oss_access_key_secret, oss_bucket_name, \
    oss_endpoint
from models.course import Category, DeviceCategory, Course, DeviceCourse
from models.course_audio import CourseAudio
from models.device import Device
from models.sms_send import SmsSend
from models.user import User
from models.user_device import User_Device
from script.mosquitto_product import send_message
from sys_utils import app, db
from utils.OSSUploader import upload_file, bucket
from utils.error_code import PARAMS_ERROR, PHONE_NUMBER_ERROR, PHONE_NOT_FIND, SUCCESS, PASSWORD_ERROR, SMS_SEND_ERROR, \
    USER_NOT_FIND, UNAUTHORIZED_ACCESS, VIDEO_UPLOAD_FAILED, SMS_CODE_ERROR, SMS_CODE_EXPIRE, \
    VIDEO_UPLOAD_NAME_REPEATED, DEVICE_NOT_FIND, VIDEO_FORMAT_ERROR
from utils.tools import ret_data, check_password, getUserIp, model_to_dict, dict_fill_url, get_location_by_ip, \
    video_resource_decrypt, video_resource_encrypt
from utils.video_utils import generate_m3u8

web_back_api = Blueprint('web_back', __name__, url_prefix='/api/v2/web_back')

@web_back_api.route('/test', methods=['GET', 'POST'])
# @jwt_required()
def test():
    #     return jsonify(ret_data(UNAUTHORIZED_ACCESS))
    return jsonify({'message': 'success'})


#用户账号手机号密码登录接口  xiaojuzi v2 20231227
@web_back_api.route('/loginByPassword', methods=['POST'])
# @decorator_sign
def loginByPassword():

    register_phone = request.form.get('register_phone', None)

    password = request.form.get('password')

    if not register_phone or not password:
        return jsonify(ret_data(PARAMS_ERROR))

    #上线得加上密码校验 20231215 xiaojuzi v2
    if not validate_password(password):
        return jsonify(ret_data(PASSWORD_ERROR))

    if not validate_phone_number(register_phone):
        return jsonify(ret_data(PHONE_NUMBER_ERROR))

    user = User.query.filter_by(register_phone=register_phone).first()

    if not user:
        return jsonify(ret_data(PHONE_NOT_FIND))

    #新增默认用户名 20231207 xiaojuzi v2 (避免v1已注册用户不生成用户名)
    if not user.nickname:
        user.nickname = generate_nickname()
        db.session.commit()

    #校验密码 20231202 xiaojuzi v2
    is_valid = check_password(password, user.password)
    if is_valid:
        user.login_count += 1
        user.uptime = datetime.now()
        user.ip = getUserIp()

        user1 = model_to_dict(user)

        db.session.commit()

        #生成令牌 20231204 xiaojuzi v2
        access_token = create_access_token(identity=user1)
        refresh_token = create_refresh_token(identity=user1)

        logging.info('user login:%s' % (user1))
        return jsonify(ret_data(SUCCESS, data={
            'message': '登录成功！',
            'access_token': access_token,
           'refresh_token': refresh_token,
        }))
    else:
        return jsonify(ret_data(PASSWORD_ERROR))

#用户手机号验证码发送验证码前查找手机号是否存在 存在则就发送短信
@web_back_api.route('/phone_is_exist', methods=['POST'])
def phone_is_exist():

    register_phone = request.form.get('register_phone', None)

    if not validate_phone_number(register_phone):
        return jsonify(ret_data(PHONE_NUMBER_ERROR))

    user = User.query.filter_by(register_phone=register_phone).first()
    if user:
        return jsonify(ret_data(SUCCESS, data={'message': '手机号已存在'}))
    else:
        return jsonify(ret_data(PHONE_NOT_FIND))


#用户手机号验证码登录 20231227 xiaojuzi v2
@web_back_api.route('/loginByPhone', methods=['POST'])
def loginByPhone():

    register_phone = request.form.get('register_phone', None)

    code = request.form.get('code', None)

    if not code:
        return jsonify(ret_data(PARAMS_ERROR))

    if not validate_phone_number(register_phone):
        return jsonify(ret_data(PHONE_NUMBER_ERROR))

    #判断验证码是否正确
    smsSend = SmsSend.query.filter_by(phone=register_phone).order_by(SmsSend.id.desc()).first()

    if not sendSms:
        return jsonify(ret_data(SMS_SEND_ERROR))

    if smsSend and (datetime.now() - smsSend.uptime).seconds < 120:
        if smsSend.code == code:

            user = User.query.filter_by(register_phone=register_phone).first()

            if user:

                # 新增默认用户名 20231207 xiaojuzi v2 (避免v1已注册用户不生成用户名)
                if not user.nickname:
                    user.nickname = generate_nickname()

                user.login_count += 1
                user.uptime = datetime.now()
                user.ip = getUserIp()

                user1 = model_to_dict(user)

                db.session.commit()

                # 生成令牌 20231204 xiaojuzi v2
                access_token = create_access_token(identity=user1)
                refresh_token = create_refresh_token(identity=user1)

                logging.info('user login:%s' % (user1))

                return jsonify(ret_data(SUCCESS, data={
                    'message': '登录成功！',
                    'access_token': access_token,
                   'refresh_token': refresh_token,
                }))
            else:
                return jsonify(ret_data(PHONE_NOT_FIND))
        else:
            return jsonify(ret_data(SMS_CODE_ERROR))
    else:
        return jsonify(ret_data(SMS_CODE_EXPIRE))

#web端查询用户信息 xiaojuzi 20231228
@web_back_api.route('/getUserInfo', methods=['POST'])
@jwt_required()
def getUserInfo():

    current_user = get_jwt_identity()
    if not current_user:
        return jsonify(ret_data(UNAUTHORIZED_ACCESS))

    # print(current_user)

    userid = current_user['openid']
    user = User.query.filter_by(openid=userid).first()

    data = model_to_dict(user)

    data = dict_fill_url(data, ['avatar'])

    location = get_location_by_ip(user.ip)

    data['location'] = location

    return jsonify(ret_data(SUCCESS, data=data))



@web_back_api.route('/getCategory', methods=['POST'])
@jwt_required()
def getCategory():

    """
    web端获取课程类别  v2 xiaojuzi
    :return: json
    """

    current_user = get_jwt_identity()

    if not current_user:
        return jsonify(ret_data(UNAUTHORIZED_ACCESS))

    openid = current_user['openid']

    # 查询用户已经绑定的设备id
    devices = User_Device.query.filter_by(userid=openid).all()

    if devices:

        # 过滤条件
        query_deviceid = db.session.query(User_Device.deviceid).filter(User_Device.userid == openid)

        query_filter=[ Category.index_cate == 1]

        query_filter.append(Device.deviceid.in_(query_deviceid))

        course_query = (db.session.query(
                Category.id,
                Category.title,
                Category.detail,
                Category.save_path,
                Category.index_cate,
                Category.priority,
                DeviceCategory.lock,
                Course.id.label('free_course_id'),
            ).join(
                DeviceCategory,
                DeviceCategory.category_id == Category.id
            ).outerjoin(
                Course,
                Course.category_id == Category.id
            ).filter(*query_filter).group_by(Category.id,DeviceCategory.lock).all())

        # 进行相同id判断为true的留下
        ids = set()
        filtered_data = []

        #遍历获取数据id
        for item in course_query:
            ids.add(item[0])

        # 遍历只要分类开放的id
        for item in course_query:
            if item[0] in ids and not item[6]:
                filtered_data.append(item)
                ids.remove(item[0])

        if ids:
            #将未开放的id 加入
            for item in course_query:
                if item[0] in ids:
                    filtered_data.append(item)
                    ids.remove(item[0])
                    if not ids:
                        break

        #返回列表
        category_list = model_to_dict(filtered_data)

        category_list = dict_fill_url(category_list, ['save_path'])

    else:
        # 未绑定设备，也展示类别，但全部锁住
        cate_objs = db.session.query(
            Category.id,
            Category.title,
            Category.detail,
            Category.save_path,
            Category.index_cate,
            Category.priority,
            Course.id.label('free_course_id'),
        ).outerjoin(
            Course, Course.category_id == Category.id
        ).filter(Category.index_cate == 1).group_by(Category.id).all()

        category_list = model_to_dict(cate_objs)
        category_list = dict_fill_url(category_list, ['save_path'])

        for cate in category_list:
            cate['lock'] = True

    return jsonify(ret_data(SUCCESS, data=category_list))


#web端查询课程信息
@web_back_api.route('/getCourse', methods=['POST'])
@jwt_required()
def getCourse():

    current_user = get_jwt_identity()

    if not current_user:
        return jsonify(ret_data(UNAUTHORIZED_ACCESS))

    openid = current_user['openid']

    course_id = request.form.get('course_id', None)
    category_id = request.form.get('category_id', None)
    course_class = request.form.get('course_class', None)

    if course_id == 'null':
        course_id = None


    # 累加设备所查询到的课程使用次数
    query_params = [Course.id, Course.title, Course.detail, Course.category_id, Course.img_files,
                    Course.priority, Course.play_time, Course.course_class, Course.volume,
                    Course.video_files,
                    cast(func.sum(DeviceCourse.use_count), Integer).label('use_count')]
    # 查询条件
    query_filter = [Course.index_show == 1]

    if category_id:
        query_filter.append(Course.category_id == int(category_id))

    if course_class:
        query_filter.append(Course.course_class == course_class)

    if course_id:
        query_filter.append(Course.id == int(course_id))

    # 过滤条件
    query_deviceid = db.session.query(User_Device.deviceid).filter(User_Device.userid == openid)

    query_filter.append(Device.deviceid.in_(query_deviceid))

    # 执行sql
    course_query = db.session.query(*query_params).join(
        DeviceCourse, DeviceCourse.course_id == Course.id
    ).join(
        Device, Device.id == DeviceCourse.device_id
    ).filter(*query_filter).group_by(Course.title)

    course_objs = course_query.all()

    if course_objs:
        course_list = model_to_dict(course_query)
        course_list = dict_fill_url(course_list, ['img_files'])

    else:
        course_list = []

    return jsonify(ret_data(SUCCESS, data=course_list))


#课程页面上传与课程相绑定的视频 xiaojuzi v2 20231228
@web_back_api.route('/upload_video', methods=['POST'])
# @jwt_required()
def upload_video():

    # current_user = get_jwt_identity()
    # if not current_user:
    #     return jsonify(ret_data(UNAUTHORIZED_ACCESS))

    files = request.files.getlist('video')

    course_id = request.form.get('course_id', None)
    course = Course.query.filter_by(id=course_id).first()

    if not course:
        return jsonify(ret_data(PARAMS_ERROR))

    try:
        if files:
            # 获取文件名和文件大小 需要人工进行名字唯一性保证 不然就没法实现断点上传
            # file_name = generate_unique_filename(file.filename)
            static_folder = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'static').replace('\\','/')
            for f in files:
                file_name = f.filename.split('.')[0]
                ext = f.filename.split('.')[1]

                if ext != 'mp4':
                    return jsonify(ret_data(VIDEO_FORMAT_ERROR))

                save_video_folder = static_folder + f'/video/{file_name}'
                video_path = os.path.join(save_video_folder, f.filename).replace('\\','/')

                if not os.path.exists(save_video_folder):
                    os.makedirs(save_video_folder)

                output_path = save_video_folder

                f.save(video_path)

                #将视频切片在上传 20240103
                ffmpeg_path = 'D:\\桌面\\ffmpeg\\ffmpeg.exe'
                ffprobe_path = 'D:\\桌面\\ffmpeg\\ffprobe.exe'

                result,ts_list = generate_m3u8(ffmpeg_path,ffprobe_path,video_path,output_path)

                if not result:
                    return jsonify(ret_data(VIDEO_UPLOAD_FAILED))

                for ts in ts_list:
                    ts_path = os.path.join(save_video_folder, ts).replace('\\','/')
                    oss_path = f"{file_name}/{ts}"
                    # print(ts_path)
                    # 上传切片文件
                    with open(ts_path, 'rb') as f1:
                        result = upload_file(oss_path, f1)
                    if result != 0:
                        return jsonify(ret_data(VIDEO_UPLOAD_FAILED))
                #上传索引文件
                index_path = os.path.join(save_video_folder, 'encrypted_slice.m3u8').replace('\\', '/')
                oss_path1 = f"{file_name}/encrypted_slice.m3u8"
                with open(index_path, 'rb') as f1:
                    result = upload_file(oss_path1, f1)
                if result != 0:
                    return jsonify(ret_data(VIDEO_UPLOAD_FAILED))

                # 将视频文件信息保存到数据库里
                if course.video_files:
                    # video_url = video_resource_decrypt(course.video_url)
                    # temp = video_url + "," + f"http://{oss_bucket_name}.oss-cn-wuhan-lr.aliyuncs.com/{file_name}"
                    # video_url_new = video_resource_encrypt(temp)
                    # course.video_url = video_url_new
                    temp = f"http://{oss_bucket_name}.oss-cn-wuhan-lr.aliyuncs.com/{file_name}"
                    #指切片从0-len(ts_list)
                    data = {"video_base_url": temp, "video_ts_list": len(ts_list)}
                    new_data = course.video_files + "," + json.dumps(data)
                    course.video_files = new_data
                else:
                    # 第一次上传视频文件
                    temp = f"http://{oss_bucket_name}.oss-cn-wuhan-lr.aliyuncs.com/{file_name}"
                    data = {"video_base_url": temp,"video_ts_list": len(ts_list)}
                    course.video_files = json.dumps(data)
                    # video_url_new = video_resource_encrypt(data)
                    # course.video_url = video_url_new

                db.session.commit()

                # print(course.video_url)
                # print(f"http://{oss_bucket_name}.oss-cn-wuhan-lr.aliyuncs.com/{file_name}")

            return jsonify(ret_data(SUCCESS,data='视频上传成功'))
        else:
            return jsonify(ret_data(PARAMS_ERROR))

    except Exception as e:
        # print(e)
        logging.info(e)
        return jsonify(ret_data(VIDEO_UPLOAD_FAILED))


#预制课发送接口 20231228 xiaojuzi v2
@web_back_api.route('/push_dat', methods=['POST'])
@jwt_required()
def videoAutoPushDatToDevice():

    current_user = get_jwt_identity()
    if not current_user:
        return jsonify(ret_data(UNAUTHORIZED_ACCESS))

    url = request.form.get('url', None)

    base_url = "/".join(url.split("/")[:-1])
    arg = url.split('/')[-2]

    if not arg or not url:
        return jsonify(ret_data(PARAMS_ERROR))

    openid = current_user['openid']

    device_list = sortDeviceByMaster(openid)

    if not device_list:
        return jsonify(ret_data(DEVICE_NOT_FIND))

    for device in device_list:

        push_json = {
            'type': 2,
            'deviceid': device.deviceid,
            'fromuser': openid,
            'message': {
                'arg': arg,
                'url': base_url
            }
        }

        logging.info(push_json)

        errcode = send_message(push_json)

    return jsonify(ret_data(errcode))


@web_back_api.route('/saveCourseAudioJson', methods=['POST'])
@jwt_required()
def saveCourseAudioJson():

    current_user = get_jwt_identity()
    if not current_user:
        return jsonify(ret_data(UNAUTHORIZED_ACCESS))

    courseId = request.form.get('courseId', None)
    audioJson = request.form.get('audioJson', None)

    if not courseId or not audioJson:
        return jsonify(ret_data(PARAMS_ERROR))

    audio = CourseAudio.query.filter_by(courseid=courseId).first()
    if audio:
        audio.audiojson = audioJson
    else:
        ca = CourseAudio(
            audiojson=audioJson,
            courseid=courseId
        )
        db.session.add(ca)

    db.session.commit()

    return jsonify(ret_data(SUCCESS, data='保存成功'))


@web_back_api.route('/getAudioJson', methods=['POST'])
@jwt_required()
def getAudioJson():

    current_user = get_jwt_identity()
    if not current_user:
        return jsonify(ret_data(UNAUTHORIZED_ACCESS))

    courseId = request.form.get('courseId', None)

    if not courseId:
        return jsonify(ret_data(PARAMS_ERROR))

    audio = CourseAudio.query.filter_by(courseid=courseId).first()

    if not audio:
        return jsonify(ret_data(SUCCESS, data="不存在该课程的视频"))

    logging.info(json.loads(audio.audiojson))

    return jsonify(ret_data(SUCCESS, data=json.loads(audio.audiojson)))





