import asyncio
import base64
import concurrent
import hashlib
import io
import json
import mmap
import multiprocessing
import os
import shutil
import subprocess
import tempfile
import threading
import time
from datetime import datetime, timedelta

import oss2
import redis
import logging

import requests
from flask import request, jsonify, Blueprint
from flask_jwt_extended import JWTManager, create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from sqlalchemy import func, cast, Integer

from api.auth import jwt_redis_blocklist
from api.miniprogram import validate_phone_number, generate_nickname, sendSms, validate_password, getDeviceByOpenid, \
    getUserSceneStrategy, getDeviceListBySceneId
from api.mqtt import sortDeviceByMaster
from config import REDIS_HOST, REDIS_DB, REDIS_PORT, oss_access_key_id, oss_access_key_secret, oss_bucket_name, \
    oss_endpoint, ffmpeg_path, ffprobe_path, HOST, JWT_ACCESS_TOKEN_EXPIRES, cdn_oss_url, SMS_EXPIRE_TIME, \
    DEVICE_EXPIRE_TIME, ADMIN_HOST
from models.admin_user import AdminUser
from models.course import Category, DeviceCategory, Course, DeviceCourse
from models.course_audio import CourseAudio
from models.device import Device
from models.device_group import DeviceGroup
from models.sms_send import SmsSend
from models.user import User
from models.user_course import User_Course
from models.user_device import User_Device
from script.mosquitto_product import send_message
from sys_utils import app, db
from utils.OSSUploader import upload_file, bucket, delete_folder
from utils.error_code import PARAMS_ERROR, PHONE_NUMBER_ERROR, PHONE_NOT_FIND, SUCCESS, PASSWORD_ERROR, SMS_SEND_ERROR, \
    USER_NOT_FIND, UNAUTHORIZED_ACCESS, VIDEO_UPLOAD_FAILED, SMS_CODE_ERROR, SMS_CODE_EXPIRE, \
    VIDEO_UPLOAD_NAME_REPEATED, DEVICE_NOT_FIND, VIDEO_FORMAT_ERROR, CHUNK_UPLOAD_EXIST, COURSE_UNBIND_VIDEO, \
    VIDEO_KEY_NOT_FIND, UNBIND_VIDEO_SCRIPT, VIDEO_UPLOAD_FAST_SUCCESS, VIDEO_IS_PROCESSING, SCENE_ERROR, LOGIN_ERROR, \
    JSON_ERROR
from utils.tools import ret_data, check_password, getUserIp, model_to_dict, dict_fill_url, get_location_by_ip, \
    video_resource_decrypt, video_resource_encrypt, paginate_data
from utils.video_utils import generate_m3u8, test_generate_m3u8, get_ts_list, getVideoDpiPath

web_back_api = Blueprint('web_back', __name__, url_prefix='/api/v2/web_back')

@web_back_api.route('/test', methods=['GET', 'POST'])
# @jwt_required()
def test():
    sceneid = request.form.getlist('sceneid')

    # device_list = getDeviceListBySceneId(sceneid)
    # print(device_list)
    #     return jsonify(ret_data(UNAUTHORIZED_ACCESS))
    return jsonify({'message': 'success'})

# 拦截请求并检查 Access Token 的过期时间 xiaojuzi v2 20240227
# @web_back_api.before_request
# def check_token_expiration():
#     current_user = get_jwt_identity()
#     if current_user is not None:
#         expires = jwt.get_expires_in()
#         if expires < 60:
#             new_access_token = create_access_token(identity=current_user)
#             # 更新用户的 Access Token
#             jwt.set_access_cookies(new_access_token)


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


#管理员登录接口 20240204 xiaojuzi v2
@web_back_api.route('/admin_login', methods=['POST'])
# @decorator_sign
def adminLogin():

    username = request.form.get('username', None)

    password = request.form.get('password')

    if not username or not password:
        return jsonify(ret_data(PARAMS_ERROR))

    user = AdminUser.query.filter_by(username=username).first()

    if not user:
        return jsonify(ret_data(PHONE_NUMBER_ERROR))

    #校验密码 20231202 xiaojuzi v2
    # print(user.password)
    is_valid = check_password(password, user.password)
    if is_valid:
        user1 = model_to_dict(user)
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

    if smsSend and (datetime.now() - smsSend.uptime).seconds < SMS_EXPIRE_TIME:
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

    if 'openid' in current_user:

        userid = current_user['openid']
        user = User.query.filter_by(openid=userid).first()

        data = model_to_dict(user)

        data = dict_fill_url(data, ['avatar'])

        location = get_location_by_ip(user.ip)

        data['location'] = location

        return jsonify(ret_data(SUCCESS, data=data))
    else:
        #管理员没有 openid 执行此处 20240218 xiaojuzi
        username = current_user['username']
        user = AdminUser.query.filter_by(username=username).first()
        return jsonify(ret_data(SUCCESS, data=model_to_dict(user)))


@web_back_api.route('/getCategory', methods=['POST'])
@jwt_required()
def getCategory():

    """
    web端获取课程类别  v2 xiaojuzi
    逻辑修改 20240130 xiaojuzi v2
    :return: json
    """

    current_user = get_jwt_identity()

    if not current_user:
        return jsonify(ret_data(UNAUTHORIZED_ACCESS))

    #展示全部类别
    cate_objs = db.session.query(
            Category.id,
            Category.title,
            Category.detail,
            Category.save_path,
            Category.index_cate,
            Category.priority
    ).filter(Category.index_cate == 1).group_by(Category.id).all()

    category_list = model_to_dict(cate_objs)
    category_list = dict_fill_url(category_list, ['save_path'])

    for cate in category_list:
        cate['lock'] = False

    return jsonify(ret_data(SUCCESS, data=category_list))


#web端查询课程信息 xiaojuzi
#逻辑修改 获取课程内容20240130 xiaojuzi v2
@web_back_api.route('/getCourse', methods=['POST'])
@jwt_required()
def getCourse():

    current_user = get_jwt_identity()

    if not current_user:
        return jsonify(ret_data(UNAUTHORIZED_ACCESS))

    phone = current_user['register_phone']

    course_id = request.form.get('course_id', None)
    category_id = request.form.get('category_id', None)
    course_class = request.form.get('course_class', None)

    if course_id == 'null':
        course_id = None

    # 查询用户可以播放此课程的使用次数
    query_params = [Course.id, Course.title, Course.detail, Course.category_id, Course.img_files,
                    Course.priority, Course.play_time, Course.course_class, Course.volume,
                    Course.video_files,User_Course.video_count]
    # 查询条件
    query_filter = [Course.index_show == 1]

    if category_id:
        query_filter.append(Course.category_id == int(category_id))

    if course_class:
        query_filter.append(Course.course_class == course_class)

    if course_id:
        query_filter.append(Course.id == int(course_id))

    #20240130 为了方便测试将测试分类的课程全部允许播放 不做限制 xiaojuzi
    # 以下代码得删掉
    # 执行sql
    # course_query = db.session.query(Course).filter(*query_filter).group_by(Course.title)
    #
    # course_objs = course_query.all()
    #
    # if course_objs:
    #     course_list = model_to_dict(course_query)
    #     course_list = dict_fill_url(course_list, ['img_files'])
    #     # 前端约定 更新该课程的video_files内的排序 20240223 xiaojuzi
    #     for cate in course_list:
    #         cate['video_count'] = 999
    #         if cate['video_files']:
    #             sorted_video_data = sorted(json.loads(cate['video_files']), key=lambda x: (int(x['episode']), -int(x['dpi'])))
    #             cate['video_files'] = json.dumps(sorted_video_data)
    # else:
    #     course_list = []
    #
    # return jsonify(ret_data(SUCCESS, data=course_list))

    #正确逻辑 xiaojuzi 20240223
    query_filter.append(User_Course.phone == phone)
    #执行sql
    course_query = db.session.query(*query_params).join(
        User_Course, Course.id == User_Course.courseid
    ).filter(*query_filter).group_by(Course.title)

    course_objs = course_query.all()

    if course_objs:
        course_list = model_to_dict(course_query)
        course_list = dict_fill_url(course_list, ['img_files'])

        #前端约定 更新该课程的video_files内的排序 20240223 xiaojuzi
        for cl in course_list:
            if cl['video_files']:
                sorted_video_data = sorted(json.loads(cl['video_files']), key=lambda x: (int(x['episode']), -int(x['dpi'])))
                cl['video_files'] = json.dumps(sorted_video_data)

    else:
        course_list = []

    return jsonify(ret_data(SUCCESS, data=course_list))



#上传视频切片处理分辨率选择  xiaojuzi v2 20240126
@web_back_api.route('/upload/getVideoDpi', methods=['GET'])
@jwt_required()
def getVideoDpi():

    current_user = get_jwt_identity()
    if not current_user:
        return jsonify(ret_data(UNAUTHORIZED_ACCESS))

    video_dpi = ['自动','360P 流畅','480P 清晰','720P 高清','1080P 全高清','原版']

    return jsonify(ret_data(SUCCESS, data=video_dpi))


#上传分块前检查分块 xiaojuzi v2 20240105
#20240118 补充相关校验到这里 逻辑更改 优化用户体验 xiaojuzi v2
@web_back_api.route('/upload/checkChunk', methods=['POST'])
@jwt_required()
def checkChunk():

    current_user = get_jwt_identity()
    if not current_user:
        return jsonify(ret_data(UNAUTHORIZED_ACCESS))

    fileMd5 = request.form.get('fileMd5', None)
    episode = request.form.get('episode', None)
    file_name = request.form.get('fileName', None)
    #20240126 视频分辨率上传新增 xiaojuzi v2
    video_dpi = request.form.get('dpi', None)

    if not fileMd5 or not episode or not file_name:
        return jsonify(ret_data(PARAMS_ERROR))

    dpi_path = getVideoDpiPath(video_dpi)
    if dpi_path is None:
        return jsonify(ret_data(PARAMS_ERROR,data='选择的dpi暂不支持！'))

    # 分块文件路径
    extension = file_name.split('.')[-1]

    if extension != 'mp4':
        return jsonify(ret_data(VIDEO_FORMAT_ERROR))

    course_id = request.form.get('courseId', None)

    course = Course.query.filter_by(id=course_id).first()

    if not course:
        return jsonify(ret_data(PARAMS_ERROR))

    data = {"episode": episode, "process_video_state": 0, "dpi": video_dpi}

    #解决多浏览器窗口下重复上传视频问题 xiaojuzi v2 20240118
    if course.process_video_state:
        # 视频处理
        data_list = json.loads(course.process_video_state)
        for video in data_list:
            #增加清晰度 20240126 xiaojuzi v2
            if video['episode'] == episode and video['dpi'] == video_dpi:
                if video['process_video_state'] != 3:
                    return jsonify(ret_data(VIDEO_IS_PROCESSING, data='视频集数的清晰度已经存在，请勿重复上传！'))
                else:
                    video['process_video_state'] = 0
                    course.process_video_state = json.dumps(data_list)
                    break
        else:
            data_list.append(data)
            course.process_video_state = json.dumps(data_list)

        db.session.commit()
    else:
        course.process_video_state = json.dumps([data])
        db.session.commit()

    static_folder = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'static').replace(
        '\\', '/')

    chunkFilePathFolder = os.path.dirname(getFilePathByMd5(fileMd5.split('-')[0], extension))

    # print(chunkFilePath)
    save_video_folder = static_folder + f'/video/{chunkFilePathFolder}'

    # temp = file_name.split('.')[0]
    # temp1 = f"http://{oss_bucket_name}.oss-cn-wuhan-lr.aliyuncs.com/{chunkFilePathFolder}"

    course = Course.query.filter_by(id=course_id).first()

    # 秒传逻辑更改 xiaojuzi v2 20240119 从redis中获取key 哈希表 dpi为key
    # jwt_redis_blocklist.hset(fileMd5.split('-')[0], "", "",ex=timedelta(days=3))
    data = jwt_redis_blocklist.hget(fileMd5.split('-')[0],video_dpi)
    if data:
        # 更新过期时间 20240123 xiaojuzi v2
        jwt_redis_blocklist.expire(fileMd5.split('-')[0],7 * 24 * 60 * 60)
        # ttl = jwt_redis_blocklist.ttl(fileMd5.split('-')[0])
        date_format = '%Y-%m-%d %H:%M:%S'
        expiry_time = (datetime.now() + timedelta(seconds=7 * 24 * 60 * 60)).strftime(date_format)
        logging.info('redis中获取到key:%s,过期时间已更新:%s' % (fileMd5.split('-')[0],expiry_time))

        data = json.loads(data)
        if course.video_files:
            data_list = json.loads(course.video_files)
            temp = {"video_base_url": data['video_base_url'], "video_ts_list": data['video_ts_list'],
                    "episode": episode, "dpi": video_dpi}
            data_list.append(temp)
            course.video_files = json.dumps(data_list)

        else:
            temp = {"video_base_url": data['video_base_url'], "video_ts_list": data['video_ts_list'],
                    "episode": episode, "dpi": video_dpi}
            course.video_files = json.dumps([temp])

        if course.process_video_path:
            # 新增逻辑 获取key必须要的路径 update by xiaojuzi v2 20240117
            data_list1 = json.loads(course.process_video_path)
            data1 = {"process_video_path": data['process_video_path'], "episode": episode,
                     "dpi": video_dpi}
            data_list1.append(data1)
            course.process_video_path = json.dumps(data_list1)
        else:
            data1 = {"process_video_path": data['process_video_path'], "episode": episode,
                     "dpi": video_dpi}
            course.process_video_path = json.dumps([data1])

        if course.process_video_state:
            data_list2 = json.loads(course.process_video_state)
            for video in data_list2:
                if video['episode'] == episode and video['dpi'] == video_dpi:
                    video['process_video_state'] = 2
                    course.process_video_state = json.dumps(data_list2)
                    break
        else:
            temp = {"episode": episode, "process_video_state": 2, "dpi": video_dpi}
            course.process_video_state = json.dumps([temp])

        db.session.commit()
        return jsonify(ret_data(VIDEO_UPLOAD_FAST_SUCCESS))

    try:
        #临时逻辑 防止碎片干扰合并不成功 20240117 xiaojuzi v2

        clear_folder = save_video_folder + f'/{dpi_path}'
        if os.path.exists(clear_folder):
            shutil.rmtree(clear_folder)

        # result = check_chunk_exist(fileMd5,save_video_folder)

        return jsonify(ret_data(SUCCESS, data='上传分片文件检查成功'))
        # if result:
        #     return jsonify(ret_data(CHUNK_UPLOAD_EXIST,data='分块文件已经存在'))
        # else:
        #     return jsonify(ret_data(SUCCESS,data='分块文件不存在'))

    except Exception as e:
        # print(e)
        logging.info('分块上传前检查异常：'+str(e))
        return jsonify(ret_data(VIDEO_UPLOAD_FAILED))


#接收前端上传的分片视频文件到本地 上传分块文件 xiaojuzi v2 20240105 课程页面上传与课程相绑定的视频
@web_back_api.route('/upload/uploadChunk', methods=['POST'])
@jwt_required()
def uploadChunk():

    current_user = get_jwt_identity()
    if not current_user:
        return jsonify(ret_data(UNAUTHORIZED_ACCESS))

    files = request.files.get('chunk')
    fileMd5 = request.form.get('fileMd5', None)
    file_name = request.form.get('fileName', None)
    #20240126 视频分辨率上传新增 xiaojuzi v2
    video_dpi = request.form.get('dpi', None)

    if not fileMd5 or not file_name:
        return jsonify(ret_data(PARAMS_ERROR))

    dpi_path = getVideoDpiPath(video_dpi)
    if dpi_path is None:
        return jsonify(ret_data(PARAMS_ERROR,data='选择的dpi暂不支持！'))

    # course_id = request.form.get('course_id', None)
    # course = Course.query.filter_by(id=course_id).first()

    # if not course:
    #     return jsonify(ret_data(PARAMS_ERROR))

    try:
        if files:
            # 获取文件名和文件大小 需要人工进行名字唯一性保证 不然就没法实现断点上传
            # file_name = generate_unique_filename(file.filename)
            static_folder = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'static').replace(
                '\\', '/')

            # 分块文件路径
            extension = file_name.split('.')[-1]

            if extension != 'mp4':
                return jsonify(ret_data(VIDEO_FORMAT_ERROR))

            file_md5 =fileMd5.split('-')[0]

            chunkFilePathFolder = os.path.dirname(getFilePathByMd5(file_md5, extension))

            # print(chunkFilePath)
            save_video_folder = static_folder + f'/video/{chunkFilePathFolder}/{dpi_path}'

            video_chunk_path = os.path.join(save_video_folder, fileMd5).replace('\\', '/')
            # print(video_chunk_path)

            if not os.path.exists(save_video_folder):
                os.makedirs(save_video_folder)

            files.save(video_chunk_path)

            return jsonify(ret_data(SUCCESS, data='视频分块上传成功'))
        else:
            return jsonify(ret_data(PARAMS_ERROR))

    except Exception as e:
        # print(e)
        logging.info('视频分块上传过程出错：' + str(e))
        # try:
        #     # 清理临时分块文件
        #     os.remove(video_chunk_path)
        # except Exception as e:
        #     print('清理临时分块文件失败：' + str(e))

        return jsonify(ret_data(VIDEO_UPLOAD_FAILED,data='视频分块上传过程出错'))

#将本地的分片视频合并加密 xiaojuzi v2 20240105
@web_back_api.route('/upload/mergeChunks', methods=['POST'])
@jwt_required()
def mergeChunks():

    current_user = get_jwt_identity()
    if not current_user:
        return jsonify(ret_data(UNAUTHORIZED_ACCESS))

    fileMd5 = request.form.get('fileMd5', None)
    file_name = request.form.get('fileName', None)
    chunkTotal = request.form.get('chunkTotal', None)
    episode = request.form.get('episode', None)

    # 20240126 视频分辨率上传新增 xiaojuzi v2
    video_dpi = request.form.get('dpi', None)


    if not fileMd5 or not file_name or not chunkTotal or not episode:
        return jsonify(ret_data(PARAMS_ERROR))

    dpi_path = getVideoDpiPath(video_dpi)
    if dpi_path is None:
        return jsonify(ret_data(PARAMS_ERROR,data='选择的dpi暂不支持！'))

    course_id = request.form.get('courseId', None)
    course = Course.query.filter_by(id=course_id).first()

    if not course:
        return jsonify(ret_data(PARAMS_ERROR))

    static_folder = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'static').replace(
        '\\', '/')

    extension = file_name.split('.')[-1]

    chunkFilePathFolder = os.path.dirname(getFilePathByMd5(fileMd5, extension))

    save_video_folder = static_folder + f'/video/{chunkFilePathFolder}/{dpi_path}'

    video_path = os.path.join(save_video_folder, file_name).replace('\\', '/')

    try:
        merged_result = merge_blobs_to_video(save_video_folder,video_path,chunkTotal)

        # print(merged_result)

        if not merged_result:
            return jsonify(ret_data(VIDEO_UPLOAD_FAILED,data='视频分块合并文件过程中出错'))

        #进行文件比对 md5值 校验
        result = check_merge_video(video_path,fileMd5)

        # print(result)
        if not result:
            return jsonify(ret_data(VIDEO_UPLOAD_FAILED,data='视频文件校验失败'))


    except Exception as e:
        # print(e)
        logging.info('视频合并文件过程中出错' + str(e))
        return jsonify(ret_data(VIDEO_UPLOAD_FAILED, data='视频合并文件过程中出错'))

    try:
        # 进行合并的文件切片加密 20240108 xiaojuzi v2
        # 获取当前事件循环对象
        # loop = asyncio.get_event_loop()
        # loop = asyncio.new_event_loop()
        # 在当前线程设置事件循环
        # asyncio.set_event_loop(loop)
        # task = loop.create_task(process_mp4_video(video_path,file_name.split('.')[0],course,episode))
        # loop.run_until_complete(task)

        # 创建后台进程来处理视频任务 20240109 xiaojuzi v2
        timer_thread = threading.Timer(5, process_mp4_video,
                                           args=(video_path, course_id, episode,video_dpi,f'{chunkFilePathFolder}/{dpi_path}'))
        timer_thread.start()

        # 视频处理中 逻辑修改20240119 xiaojuzi v2
        # course.process_video_state = 1

        if course.process_video_path:
            data_list = json.loads(course.process_video_path)
            for video in data_list:
                if video['episode'] == episode and video['dpi'] == video_dpi:
                    video['process_video_path'] = video_path
                    course.process_video_path = json.dumps(data_list)
                    break
            else:
                data = {"process_video_path": video_path, "episode": episode,"dpi": video_dpi}
                data_list.append(data)
                # new_data = course.process_video_path + "," + json.dumps(data)
                course.process_video_path = json.dumps(data_list)
                # print(course.process_video_path)

        else:
            data = {"process_video_path": video_path, "episode": episode,"dpi": video_dpi}
            course.process_video_path = json.dumps([data])

            # print(course.process_video_path)

        if course.process_video_state:
            data_list1 = json.loads(course.process_video_state)
            for video in data_list1:
                if video['episode'] == episode and video['dpi'] == video_dpi:
                    video['process_video_state'] = 1
                    course.process_video_state = json.dumps(data_list1)
                    break
            else:
                data = {"episode": episode, "process_video_state": 1,"dpi": video_dpi}
                data_list1.append(data)
                course.process_video_state = json.dumps(data_list1)
        else:
            data = {"episode": episode, "process_video_state": 1,"dpi": video_dpi}
            course.process_video_state = json.dumps([data])

        db.session.commit()

    except Exception as e:
        # print(e)
        logging.info('视频异步处理过程中出错:' + str(e))
        return jsonify(ret_data(VIDEO_UPLOAD_FAILED, data='视频异步处理过程中出错'))

    #不等待视频处理任务结束直接返回
    return jsonify(ret_data(SUCCESS,data='视频合并成功'))


# 上传视频获取所有课程分类  xiaojuzi v2 20240109
@web_back_api.route('/getCourseCategory', methods=['GET'])
@jwt_required()
def getCourseCategory():
    current_user = get_jwt_identity()
    if not current_user:
        return jsonify(ret_data(UNAUTHORIZED_ACCESS))

    category = Category.query.all()

    if not category:
        return jsonify(ret_data(PARAMS_ERROR))

    category_list = model_to_dict(category)
    category_list = dict_fill_url(category_list, ['save_path'])

    logging.info('获取课程分类成功: %s' % category_list)

    return jsonify(ret_data(SUCCESS, data=category_list))

#上传视频获取课程分类下所有课程内容 xiaojuzi v2 20240109
@web_back_api.route('/getCourseByCategoryId', methods=['POST'])
@jwt_required()
def getCourseByCategoryId():

    current_user = get_jwt_identity()
    if not current_user:
        return jsonify(ret_data(UNAUTHORIZED_ACCESS))

    category_id = request.form.get('categoryId', None)

    if not category_id:
        return jsonify(ret_data(PARAMS_ERROR))

    course = Course.query.filter_by(category_id=category_id).all()

    if not course:
        return jsonify(ret_data(PARAMS_ERROR))

    course_list = model_to_dict(course)
    course_list = dict_fill_url(course_list, ['img_files'])

    logging.info('获取课程内容成功: %s' % course_list)

    return jsonify(ret_data(SUCCESS, data=course_list))


#20240111 xiaojuzi v2 后台管理系统 课程管理 课程内容多条件筛选 增加分页查询
@web_back_api.route('/getCourseByMultipleConditions', methods=['POST'])
@jwt_required()
def getCourseByMultipleConditions():

    current_user = get_jwt_identity()
    if not current_user:
        return jsonify(ret_data(UNAUTHORIZED_ACCESS))

    course_title = request.form.get('courseTitle', None)
    course_category = request.form.get('courseCategory', None)
    course_id = request.form.get('course_id', None)

    page_size = request.form.get('pageSize',0)
    page_number = request.form.get('pageNumber',0)

    page_size = int(page_size)
    page_number = int(page_number)


    if course_id == 'null':
        course_id = None

    query_params = [Course.id, Course.title, Course.detail, Course.category_id,Category.title.label('category_title'),
                    Course.save_path,Course.img_files,Course.data_files,Course.lrc_files,Course.voice_files,
                    Course.index_show,Course.priority, Course.play_time, Course.course_class, Course.volume,
                    Course.video_files, Course.process_video_state]
    # 查询条件
    query_filter = []

    if course_title:
        query_filter.append(Course.title.like(f"%{course_title}%"))

    if course_category:
        query_category_id = db.session.query(Category.id).filter(Category.title.like(f"%{course_category}%")).subquery()
        query_filter.append(Course.category_id.in_(query_category_id))

    if course_id:
        query_filter.append(Course.id == int(course_id))

    # 执行sql
    course_query = (db.session.query(*query_params).filter(*query_filter).outerjoin(Category, Category.id == Course.category_id).group_by(Course.title))

    course_objs = course_query.all()

    if course_objs:
        course_list = model_to_dict(course_objs)

        course_list = dict_fill_url(course_list, ['img_files', 'data_files', 'lrc_files','voice_files'])

        if page_size > 0 and page_number > 0:
            # 对数据分页
            select_data_list = paginate_data(course_list, page_size, page_number)

            # logging.info('课程内容筛选成功: %s' % select_data_list)

            return jsonify({
                'errcode': SUCCESS,
                'total_count': len(course_list),
                'page_size': page_size,
                'page_number': page_number,
                'total': len(select_data_list),
                'data': select_data_list
            })

        # logging.info('课程内容筛选成功: %s' % course_list)
        return jsonify(ret_data(SUCCESS, data=course_list))
    else:
        course_list = []
        # logging.info('课程内容筛选成功: %s' % course_list)
        return jsonify(ret_data(SUCCESS, data=course_list))


#校验合并的原视频和分片视频的是否一致 xiaojuzi v2 20240105
def check_merge_video(video_file,fileMd5):

    try:
        if not os.path.exists(video_file):
            return False

        # 计算原视频文件的MD5哈希值
        # 打开视频文件并进行内存映射
        with open(video_file, 'rb') as file:
            # 创建内存映射对象
            mmapped_file = mmap.mmap(file.fileno(), 0, access=mmap.ACCESS_READ)

            # 计算原视频文件的MD5哈希值
            md5_hash = hashlib.md5(mmapped_file)

            # 获取计算得到的MD5值
            calculated_md5 = md5_hash.hexdigest()

            # 关闭内存映射对象
            mmapped_file.close()

        # print(calculated_md5)
        # print(fileMd5)

        # 比较计算得到的MD5值与预期的MD5值
        if calculated_md5 == fileMd5:
            return True
            # print('视频文件校验通过')
            logging.info('视频文件校验通过')
        else:
            logging.info('视频文件校验失败')
            # print('视频文件校验失败')
            return False
    except Exception as e:
        # print(e)
        logging.info('视频文件校验异常' + str(e))
        return False

#检查分块是否存在 分块上传前检查 xiaojuzi v2 20240105
def check_chunk_exist(fileMd5,directory):
    for filename in os.listdir(directory):
        if filename == fileMd5:
            return True
    return False


#获取分片视频所有的blob对象 进行合并操作 xiaojuzi v2 20240105
def merge_blobs_to_video(directory,video_path,chunkTotal):
    try:
        # 创建一个空的视频列表
        video_files = os.listdir(directory)
        logging.info('分块文件合并方法，原块数：%s,接收块数：%s' % (chunkTotal, len(video_files)))
        # 逐个处理每个 blob 文件
        # for filename in os.listdir(directory):
        #     if filename.endswith('.mp4'):
        #         continue
        #     # 将分块文件添加到列表中
        #     video_files.append(filename)

        # print(video_files)

        if int(len(video_files)) != int(chunkTotal):
            logging.info('分块文件数量与预期不一致 原块数：%s,接收块数：%s' %(chunkTotal,len(video_files)))
            return False

        fileMd5 = video_files[0].split('-')[0]

        # print(fileMd5)

        # print(video_files)
        # 使用 ffmpeg 工具合并视频文件
        # command = [ffmpeg_path, '-i', 'concat:' + '|'.join(video_files), '-c', 'copy', video_path]
        # subprocess.call(command)

        with open(video_path, 'wb') as merged_file:
            for i in range(len(video_files)):
                file1 = f'{fileMd5}-{str(i)}'
                filepath = os.path.join(directory, file1).replace('\\', '/')
                with open(filepath, 'rb') as f:
                    merged_file.write(f.read())

        # with open(video_path, 'ab') as merged_file:
        #     for filename in os.listdir(directory):
        #         filepath = os.path.join(directory, filename).replace('\\', '/')
        #         # print(filepath)
        #         if os.path.isfile(filepath):
        #             with open(filepath, 'rb') as file:
        #                 merged_file.write(file.read())

        return True
    except Exception as e:
        # print(e)
        logging.info('合并分块文件失败：' + str(e))
        try:
            # 清理临时视频文件
            os.remove(video_path)
        except Exception as e:
            # print('清理临时视频文件失败：'+str(e))
            logging.info('清理临时视频文件失败：' + str(e))

        return False
    #暂时注掉 20240119 xiaojuzi
    finally:
        try:
            # 清理临时分块文件
            for file in video_files:
                filepath = os.path.join(directory, file).replace('\\', '/')
                os.remove(filepath)
        except Exception as e:
            # print('清理临时分块文件失败：'+str(e))
            logging.info('清理临时分块文件失败：'+str(e))



#根据MD5和文件扩展名，生成文件路径 xiaojuzi v2 20240105
def getFilePathByMd5(fileMd5: str,extension: str):

    return f"{fileMd5[0:1]}/{fileMd5[1:2]}/{fileMd5}/{fileMd5}+'.'+{extension}"


#处理mp4视频将其切片且加密并上传到OSS xiaojuzi v2 20240105 逻辑修改20240119 xiaojuzi v2
def process_mp4_video(video_path,course_id,episode,video_dpi,chunkFilePathFolder):

    with app.app_context():
        # print('已经开始视频处理')
        logging.info('开始视频处理,课程id：%s，集数：%s,分辨率：%s'%(course_id,episode,video_dpi))
        save_video_folder = os.path.dirname(video_path)

        # 将视频切片在上传 20240103
        # ffmpeg_path = 'D:\\桌面\\ffmpeg\\ffmpeg.exe'
        # ffprobe_path = 'D:\\桌面\\ffmpeg\\ffprobe.exe'

        # result, ts_list = generate_m3u8(ffmpeg_path, ffprobe_path, video_path, save_video_folder)
        result, ts_list = test_generate_m3u8(ffmpeg_path, ffprobe_path, video_path, save_video_folder,video_dpi)

        # print(result)
        # print(ts_list)
        course = Course.query.filter_by(id=course_id).first()
        if not result:
            #视频处理出错
            data_list = json.loads(course.process_video_state)
            for video in data_list:
                if video['episode'] == episode and video['dpi'] == video_dpi:
                    video['process_video_state'] = 3
                    course.process_video_state = json.dumps(data_list)
                    break
            else:
                data = {"episode": episode, "process_video_state": 3,"dpi": video_dpi}
                data_list.append(data)
                course.process_video_state = json.dumps(data_list)

            db.session.commit()
            return VIDEO_UPLOAD_FAILED

        upload_ts = []
        for ts in ts_list:
            ts_path = os.path.join(save_video_folder, ts).replace('\\', '/')
            oss_path = f"{chunkFilePathFolder}/{ts}"
            # print(ts_path)
            # 上传切片文件
            with open(ts_path, 'rb') as f1:
                result = upload_file(oss_path, f1)
                # print(result)
                if result != 0:
                    # 视频上传出错 再上传一次 20240119 xiaojuzi v2
                    result1 = upload_file(oss_path, f1)
                    if result1 != 0:
                        upload_ts.append(0)
                        # 视频处理出错
                        data_list = json.loads(course.process_video_state)
                        for video in data_list:
                            if video['episode'] == episode and video['dpi'] == video_dpi:
                                if video['process_video_state'] != 4:
                                    video['process_video_state'] = 4
                                    course.process_video_state = json.dumps(data_list)
                                break
                        else:
                            data = {"episode": episode, "process_video_state": 4,"dpi" : video_dpi}
                            data_list.append(data)
                            course.process_video_state = json.dumps(data_list)
                    else:
                        upload_ts.append(1)
                    # upload_ts.append(0)
                # db.session.commit()
                else:
                    upload_ts.append(1)
                # return VIDEO_UPLOAD_FAILED

        # 上传索引文件
        index_path = os.path.join(save_video_folder, 'encrypted_slice.m3u8').replace('\\', '/')
        oss_path1 = f"{chunkFilePathFolder}/encrypted_slice.m3u8"
        with open(index_path, 'rb') as f1:
            # print(result)
            result = upload_file(oss_path1, f1)
            if result != 0:
                # 视频上传出错 再上传一次 20240119 xiaojuzi v2
                result1 = upload_file(oss_path1, f1)
                if result1 != 0:
                    upload_ts.append(0)
                    # 视频处理出错
                    data_list = json.loads(course.process_video_state)
                    for video in data_list:
                        if video['episode'] == episode and video['dpi'] == video_dpi:
                            if video['process_video_state'] != 4:
                                video['process_video_state'] = 4
                                course.process_video_state = json.dumps(data_list)
                            break
                    else:
                        data = {"episode": episode, "process_video_state": 4,"dpi" : video_dpi}
                        data_list.append(data)
                        course.process_video_state = json.dumps(data_list)
                else:
                    upload_ts.append(1)
                # upload_ts.append(0)
            # db.session.commit()
            else:
                upload_ts.append(1)
            # return VIDEO_UPLOAD_FAILED

        #写入上传状况文件 记录日志 在此之前会自动重传一次还不成功就只能手动上传 xiaojuziv2 20240119
        upload_result = os.path.join(save_video_folder, 'upload_file.txt').replace('\\', '/')
        with open(upload_result, 'w') as f:
            for i in upload_ts:
                f.write(str(i) + "\n")

        cache_data = {"video_base_url": "", "video_ts_list": "", "process_video_path": ""}
        #将视频文件信息保存到数据库里 逻辑修改20240119 xiaojuzi v2
        if course.video_files:
            # video_url = video_resource_decrypt(course.video_url)
            # temp = video_url + "," + f"http://{oss_bucket_name}.oss-cn-wuhan-lr.aliyuncs.com/{file_name}"
            # video_url_new = video_resource_encrypt(temp)
            # course.video_url = video_url_new
            #新增cdn 20240126 xiaojuzi v2
            temp = f"{cdn_oss_url}/{chunkFilePathFolder}"
            # 指切片从0-len(ts_list)
            data_list = json.loads(course.video_files)
            for video in data_list:
                if video['episode'] == episode and video['dpi'] == video_dpi:
                    video['video_base_url'] = temp
                    video['video_ts_list'] = len(ts_list)
                    course.video_files = json.dumps(data_list)

                    cache_data['video_base_url'] = temp
                    cache_data['video_ts_list'] = len(ts_list)
                    break
            else:
                data = {"video_base_url": temp, "video_ts_list": len(ts_list),
                        "episode": episode,"dpi": video_dpi}
                # new_data = course.video_files + "," + json.dumps(data)
                data_list.append(data)
                course.video_files = json.dumps(data_list)

                cache_data['video_base_url'] = temp
                cache_data['video_ts_list'] = len(ts_list)
        else:
            # 第一次上传视频文件
            temp = f"{cdn_oss_url}/{chunkFilePathFolder}"
            data = {"video_base_url": temp, "video_ts_list": len(ts_list),
                    "episode": episode,"dpi" : video_dpi}
            # data_str = '[' + data + ']'
            course.video_files = json.dumps([data])

            cache_data['video_base_url'] = temp
            cache_data['video_ts_list'] = len(ts_list)

            # video_url_new = video_resource_encrypt(data)
            # course.video_url = video_url_new


        #更改视频处理状态
        data_list1 = json.loads(course.process_video_state)
        for video in data_list1:
            if video['episode'] == episode and video['dpi'] == video_dpi:
                video['process_video_state'] = 2
                course.process_video_state = json.dumps(data_list1)
                break
        else:
            data = {"episode": episode, "process_video_state": 2,"dpi": video_dpi}
            data_list1.append(data)
            course.process_video_state = json.dumps(data_list1)
        # course.process_video_state = 2

        data_list2 = json.loads(course.process_video_path)
        for video in data_list2:
            if video['episode'] == episode and video['dpi'] == video_dpi:
                cache_data['process_video_path'] = video['process_video_path']
                break

        db.session.commit()

        #都完成存储到redis中作为全后台秒传缓存
        jwt_redis_blocklist.hset(chunkFilePathFolder.split('/')[-2],video_dpi,json.dumps(cache_data))
        jwt_redis_blocklist.expire(chunkFilePathFolder.split('/')[-2],timedelta(days=7))

        # print(course.video_url)
        # print(f"http://{oss_bucket_name}.oss-cn-wuhan-lr.aliyuncs.com/{file_name}")

#获取视频加密key接口 20240108 xiaojuzi v2
@web_back_api.route('/getVideoKey', methods=['POST'])
@jwt_required()
def getVideoKey():

    current_user = get_jwt_identity()
    if not current_user:
        return jsonify(ret_data(UNAUTHORIZED_ACCESS))

    episode = request.form.get('episode', None)

    if not episode:
        return jsonify(ret_data(PARAMS_ERROR))

    video_dpi = request.form.get('dpi', None)

    dpi_path = getVideoDpiPath(video_dpi)
    if dpi_path is None:
        return jsonify(ret_data(PARAMS_ERROR,data='选择的dpi暂不支持！'))

    course_id = request.form.get('courseId', None)
    course = Course.query.filter_by(id=course_id).first()

    if not course:
        return jsonify(ret_data(PARAMS_ERROR))

    # 在字符串前后添加方括号，使其成为一个有效的 JSON 列表
    # data_str = '[' + course.process_video_path + ']'

    data_list = json.loads(course.process_video_path)
    # print(data_list)

    process_video_path = None

    for data_dict in data_list:
        if "episode" in data_dict and data_dict['episode'] == str(episode) and data_dict['dpi'] == video_dpi:
            process_video_path = data_dict['process_video_path']
            break

    if not process_video_path:
        return jsonify(ret_data(COURSE_UNBIND_VIDEO))

    fileMd5 = process_video_path.split('/')[-3]
    # print(fileMd5)

    static_folder = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'static').replace(
        '\\', '/')

    key_path = f'video/{str(fileMd5[0:1])}/{fileMd5}/{dpi_path}/keyinfo.txt'
    key = os.path.join(static_folder, key_path).replace('\\', '/')

    if not os.path.exists(key):
        return jsonify(ret_data(VIDEO_KEY_NOT_FIND))

    with open(key, 'r') as f:
        keyinfo = f.read().splitlines()

    encrypt_path = HOST + f'/video/{str(fileMd5)[0:1]}/{fileMd5}/{dpi_path}/encrypt.key'

    return jsonify(ret_data(SUCCESS, data={
        'iv': keyinfo[2],
        'encrypt_path': encrypt_path
    }))

#获取课程视频列表接口 20240118 xiaojuzi v2
@web_back_api.route('/getCourseVideoListByCourseId', methods=['POST'])
@jwt_required()
def getCourseVideoListByCourseId():

    current_user = get_jwt_identity()
    if not current_user:
        return jsonify(ret_data(UNAUTHORIZED_ACCESS))

    course_id = request.form.get('courseId', None)
    course = Course.query.filter_by(id=course_id).first()

    if not course:
        return jsonify(ret_data(PARAMS_ERROR))

    data_list = []
    # unique_episodes = set()
    video_data = None
    if course.video_files:
        video_data = json.loads(course.video_files)
    # if course.video_files:
    #     temp = json.loads(course.video_files)
    #     for video in temp:
    #         if video['episode'] not in unique_episodes:
    #             unique_episodes.add(video['episode'])
    #             video_data.append(video)

    if course.process_video_state:
        data = {"video_base_url": "",
                "episode": "",
                "dpi": "",
                "video_ts_list": "",
                "process_video_state": ""}

        state_data = json.loads(course.process_video_state)
        # unique_episodes.clear()
        for state in state_data:
            if video_data:
                for video in video_data:
                    if video['episode'] == state['episode'] and video['dpi'] == state['dpi']:
                        data['video_base_url'] = video['video_base_url']
                        data['video_ts_list'] = video['video_ts_list']
                        data['process_video_state'] = state['process_video_state']
                        data['episode'] = state['episode']
                        data['dpi'] = state['dpi']
                        data_list.append(data)

                        # unique_episodes.add(state['episode'])
                        video_data.remove(video)
                        break
                else:
                    data['video_base_url'] = ""
                    data['video_ts_list'] = ""
                    data['process_video_state'] = state['process_video_state']
                    data['episode'] = state['episode']
                    data['dpi'] = state['dpi']
                    data_list.append(data)

                # 清除数据 创建新的字典对象
                data = {"video_base_url": "",
                        "episode": "",
                        "dpi": "",
                        "video_ts_list": "",
                        "process_video_state": ""}

            else:
                data['video_base_url'] = ""
                data['video_ts_list'] = ""
                data['process_video_state'] = state['process_video_state']
                data['episode'] = state['episode']
                data['dpi'] = state['dpi']
                data_list.append(data)

                # 清除数据 创建新的字典对象
                data = {"video_base_url": "",
                        "episode": "",
                        "dpi": "",
                        "video_ts_list": "",
                        "process_video_state": ""}

        sorted_data_list = sorted(data_list, key=lambda x: (int(x['episode']), -int(x['dpi'])))

        return jsonify(ret_data(SUCCESS, data=sorted_data_list))

    else:
        return jsonify(ret_data(SUCCESS, data=data_list))


#预制课发送接口 20231228 xiaojuzi v2
# 需要前端传递设置的设备  定为场景id方便管理 20240131
# 20240313 重构优化此方法 xiaojuzi v2
@web_back_api.route('/push_dat', methods=['POST'])
@jwt_required()
def videoAutoPushDatToDevice():

    current_user = get_jwt_identity()
    if not current_user:
        return jsonify(ret_data(UNAUTHORIZED_ACCESS))

    url = request.form.get('url', None)
    #20240204 xiaojuzi v2  修改
    sceneid = request.form.get('sceneid')

    if not url or not sceneid:
        return jsonify(ret_data(PARAMS_ERROR))

    #updateby xiaojuzi v2 20240131
    openid = current_user['openid']

    #先进行dat文件判断是否已经下载过 20240313 xiaojuzi
    # 20240124 xiaojuzi v2 因不同平台协调问题 按领导方案修改逻辑
    static_folder = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'static').replace('\\',
                                                                                                                '/')
    # 更新新名字截取格式 20240225 xiaojuzi v2
    file_name = ''.join(url.split('/')[-1].split('.')[0].split('-')[:5])

    # 要保存的文件的文件夹
    save_file_folder = static_folder + f'/test/{file_name}'

    if not os.path.exists(save_file_folder):
        os.makedirs(save_file_folder)

        # file_name = ''.join(url.split('/')[-1].split('.')[0])
        save_file_dat = os.path.join(save_file_folder, f'{file_name}.dat').replace("\\", "/")
        temp_file_lrc = os.path.join(save_file_folder, f'{file_name}.lrc').replace("\\", "/")

        #下载文件
        flag = getDownloadFileToLocal(url, save_file_dat,temp_file_lrc)

        if not flag:
            return jsonify(ret_data(PARAMS_ERROR))


    #20240220 xiaojuzi 修改前端传递格式
    sceneid = json.loads(sceneid)

    device_list = getDeviceListBySceneId(sceneid)

    if not device_list:
        return jsonify(ret_data(DEVICE_NOT_FIND))

    for device in device_list:
        #20240223 新需求更改 xiaojuzi 记录 添画需要判断过否在线  20240308 不管在不在线直接发 暂时修改
        # device1 = Device.query.filter_by(deviceid=device.deviceid).first()
        # if (int(datetime.now().timestamp()) - device1.status_update.timestamp() <= DEVICE_EXPIRE_TIME):

        push_json = {
            'type': 2,
            'deviceid': device.deviceid,
            'fromuser': openid,
            'message': {
                'arg': file_name,
                'url': HOST + f'/test/{file_name}'
            }
        }

        logging.info(push_json)

        errcode = send_message(push_json)

        logging.info('push_dat发送的result：%s ' % errcode)

    return jsonify(ret_data(SUCCESS))


# 下载文件到本地 xiaojuzi 20240313
def getDownloadFileToLocal(url,file_path,temp_file):

    response = requests.get(url)

    if response.status_code == 200:
        if not response.content:
            logging.info("下载失败，数据为空！")
            return False
        # 如果请求成功，将文件内容写入本地文件
        with open(file_path, 'wb') as f:
            f.write(response.content)
            logging.info("文件保存成功:%s" % file_path)

        with open(temp_file, 'w') as file:
            file.write('000000000000000000000000000000000')

        return True
    else:
        logging.info("下载失败，状态码:%s" % response.status_code)
        return False


#保存在线视频课程脚本接口  update 20240112  by xiaojuzi v2
@web_back_api.route('/saveCourseAudioJson', methods=['POST'])
@jwt_required()
def saveCourseAudioJson():

    current_user = get_jwt_identity()
    if not current_user:
        return jsonify(ret_data(UNAUTHORIZED_ACCESS))

    courseId = request.form.get('courseId', None)
    audioJson = request.form.get('audioJson', None)
    episode = request.form.get('episode', None)

    if not courseId or not audioJson or not episode:
        return jsonify(ret_data(PARAMS_ERROR))

    audioJson = json.loads(audioJson)

    audio = CourseAudio.query.filter_by(courseid=courseId, episode=episode).first()
    if audio:
        data_list = json.loads(audio.audiojson)
        for ad in audioJson:
            data_list['timePoint'].append(ad)

        audio.audiojson = json.dumps(data_list)

        logging.info("新增视频脚本成功：%s" % (audioJson))
    else:
        data_dict = {
            "courseId": courseId,
            "episode": episode,
            "timePoint": audioJson,
        }
        ca = CourseAudio(
            audiojson=json.dumps(data_dict),
            episode=episode,
            courseid=courseId
        )
        db.session.add(ca)
        logging.info("新增视频脚本成功：%s" % (data_dict))

    db.session.commit()

    return jsonify(ret_data(SUCCESS, data='保存成功'))


#根据课程id查询视频脚本  update by 20240112 xiaojuzi v2
@web_back_api.route('/getAudioJson', methods=['POST'])
@jwt_required()
def getAudioJsonByCourseId():

    current_user = get_jwt_identity()
    if not current_user:
        return jsonify(ret_data(UNAUTHORIZED_ACCESS))

    courseId = request.form.get('courseId', None)
    episode = request.form.get('episode', None)

    if not courseId or not episode:
        return jsonify(ret_data(PARAMS_ERROR))

    audio = CourseAudio.query.filter_by(courseid=courseId, episode=episode).first()

    if not audio:
        return jsonify(ret_data(UNBIND_VIDEO_SCRIPT))

    data_list = json.loads(audio.audiojson)

    # logging.info("课程脚本查询成功：%s" % data_list)

    return jsonify(ret_data(SUCCESS, data=data_list))


#删除课程id下的某个视频脚本 20240113 xiaojuzi v2
@web_back_api.route('/deleteAudioJsonByCourseId', methods=['POST'])
@jwt_required()
def deleteAudioJsonByCourseId():

    current_user = get_jwt_identity()
    if not current_user:
        return jsonify(ret_data(UNAUTHORIZED_ACCESS))

    courseId = request.form.get('courseId', None)
    episode = request.form.get('episode', None)
    timestamp = request.form.get('timeId', None)


    if not courseId or not episode:
        return jsonify(ret_data(PARAMS_ERROR))

    audio = CourseAudio.query.filter_by(courseid=courseId, episode=episode).first()

    if not audio:
        return jsonify(ret_data(UNBIND_VIDEO_SCRIPT))

    data_list = json.loads(audio.audiojson)

    for data in data_list['timePoint']:
        if data['timeId'] == timestamp:
            data_list['timePoint'].remove(data)
            break
    # db.session.delete(audio)
    audio.audiojson = json.dumps(data_list)
    db.session.commit()

    return jsonify(ret_data(SUCCESS, data='删除成功'))


#修改课程id下某个视频脚本 20240113 xiaojuzi v2
@web_back_api.route('/updateAudioJsonByCourseId', methods=['POST'])
@jwt_required()
def updateAudioJsonByCourseId():

    current_user = get_jwt_identity()
    if not current_user:
        return jsonify(ret_data(UNAUTHORIZED_ACCESS))

    courseId = request.form.get('courseId', None)
    episode = request.form.get('episode', None)
    timestamp = request.form.get('timeId', None)

    sendType = request.form.get('sendType', None)
    startTime = request.form.get('startTime', None)
    formatStartTime = request.form.get('formatStartTime', None)
    endTime = request.form.get('endTime', None)
    marks = request.form.get('marks', None)
    data1 = request.form.get('data', None)

    if not courseId or not episode:
        return jsonify(ret_data(PARAMS_ERROR))

    audio = CourseAudio.query.filter_by(courseid=courseId, episode=episode).first()

    if not audio:
        return jsonify(ret_data(UNBIND_VIDEO_SCRIPT))

    data_list = json.loads(audio.audiojson)

    for data in data_list['timePoint']:
        if data['timeId'] == timestamp:
            if sendType:
                data['sendType'] = sendType
            if startTime:
                data['startTime'] = startTime
            if endTime:
                data['endTime'] = endTime
            if formatStartTime:
                data['formatStartTime'] = formatStartTime
            if marks:
                data['marks'] = marks
            if data1:
                data['data'] = json.loads(data1)
            break
    # db.session.delete(audio)
    audio.audiojson = json.dumps(data_list)
    db.session.commit()

    return jsonify(ret_data(SUCCESS, data='修改成功'))

#删除课程绑定的视频 20240116 xiaojuzi v2 更改逻辑 20240119 xiaojuzi v2
@web_back_api.route('/deleteVideoByCourseId', methods=['POST'])
@jwt_required()
def deleteVideoByCourseId():

    current_user = get_jwt_identity()
    if not current_user:
        return jsonify(ret_data(UNAUTHORIZED_ACCESS))

    courseId = request.form.get('courseId', None)
    episode = request.form.get('episode', None)

    if not courseId or not episode:
        return jsonify(ret_data(PARAMS_ERROR))

    course = Course.query.filter_by(id=courseId).first()

    if not course:
        return jsonify(ret_data(PARAMS_ERROR))

    video_dpi = request.form.get('dpi', None)

    dpi_path = getVideoDpiPath(video_dpi)
    if dpi_path is None:
        return jsonify(ret_data(PARAMS_ERROR,data='选择的dpi暂不支持！'))

    data_list = None
    data_list1 = None

    if course.video_files:
        data_list = json.loads(course.video_files)
    if course.process_video_state:
        data_list1 = json.loads(course.process_video_state)

    flag = True

    if data_list1:
        for data1 in data_list1:
            if data1['episode'] == episode and data1['dpi'] == video_dpi:
                data_list1.remove(data1)
                flag = False
                if len(data_list1) == 0:
                    course.process_video_state = None
                else:
                    course.process_video_state = json.dumps(data_list1)
                break

    if data_list:
        for data in data_list:
            if data['episode'] == episode and data['dpi'] == video_dpi:
                # folder = data['video_base_url'].split('/')[-1]
                # print(folder)
                # delete_folder(folder)
                # print(result)
                data_list.remove(data)

                flag = False
                # print(len(data_list))
                if len(data_list) == 0:
                    course.video_files = None
                else:
                    course.video_files = json.dumps(data_list)

                break

    if flag:
        return jsonify(ret_data(PARAMS_ERROR,data="该课程没有此视频集数！"))

    #删除本地文件数据
    data_list2 = None
    if course.process_video_path:
        data_list2 = json.loads(course.process_video_path)
    if data_list2:
        for data in data_list2:
            if data['episode'] == episode and data['dpi'] == video_dpi:
                # folder = '/'.join(data['process_video_path'].split('/')[:-1])
                # print(folder)
                # shutil.rmtree(folder)
                data_list2.remove(data)
                # print(len(data_list1))
                if len(data_list2) == 0:
                    course.process_video_path = None
                else:
                    course.process_video_path = json.dumps(data_list2)

                break

    db.session.commit()

    return jsonify(ret_data(SUCCESS, data='删除视频成功'))

#课程绑定视频手动重新上传 20240119 xiaojuzi v2
@web_back_api.route('/restartUploadVideoByCourseId', methods=['POST'])
@jwt_required()
def restartUploadVideoByCourseId():

    current_user = get_jwt_identity()
    if not current_user:
        return jsonify(ret_data(UNAUTHORIZED_ACCESS))

    courseId = request.form.get('courseId', None)
    episode = request.form.get('episode', None)

    if not courseId or not episode:
        return jsonify(ret_data(PARAMS_ERROR))

    course = Course.query.filter_by(id=courseId).first()

    if not course:
        return jsonify(ret_data(PARAMS_ERROR))

    video_dpi = request.form.get('dpi', None)

    dpi_path = getVideoDpiPath(video_dpi)
    if dpi_path is None:
        return jsonify(ret_data(PARAMS_ERROR,data='选择的dpi暂不支持！'))


    if course.process_video_path:
        data_list = json.loads(course.process_video_path)
        for data in data_list:
            if data['episode'] == episode and data['dpi'] == video_dpi:
                folder = "/".join(data['process_video_path'].split('/')[:-1])
                path = os.path.join(folder,'upload_file.txt').replace('\\','/')
                temp =data['process_video_path'].split('/')[-1]

                file_name = temp.split('.')[:-1]

                if not os.path.exists(path):
                    return jsonify(ret_data(PARAMS_ERROR,data="视频还未处理完毕或处理错误，未进行上传文件日志生成！"))

                with open(path,'r') as f:
                    content = f.read().splitlines()

                ts_list = get_ts_list(os.path.join(folder, 'encrypted_slice.m3u8').replace("\\", "/"))

                for i,n in enumerate(content):

                    if i == len(content)-1:
                        index_path = os.path.join(folder, 'encrypted_slice.m3u8').replace('\\', '/')
                        oss_path1 = f"{file_name}/encrypted_slice.m3u8"
                        with open(index_path, 'rb') as f1:
                            result = upload_file(oss_path1, f1)
                            if result == 0:
                                content[i] = 1

                    if n == str(0) and i != len(content)-1:

                        ts_path = os.path.join(folder, ts_list[i]).replace('\\', '/')
                        oss_path = f"{file_name}/{ts_list[i]}"
                        # 上传切片文件
                        with open(ts_path, 'rb') as f1:
                            result = upload_file(oss_path, f1)
                            if result == 0:
                                content[i] = 1

                #重新写入上传文件日志
                flag = True
                with open(path, 'w') as f:
                    for i in content:
                        if i == str(0):
                            flag = False
                        f.write(str(i) + "\n")

                if flag:
                    data_list = json.loads(course.process_video_state)
                    for video in data_list:
                        if video['episode'] == episode and video['dpi'] == video_dpi:
                            video['process_video_state'] = 2
                            course.process_video_state = json.dumps(data_list)
                            db.session.commit()
                            break

    return jsonify(ret_data(SUCCESS, data='重新上传视频成功'))


#web端修改用户课程视频次数信息 20240130 xiaojuzi v2
@web_back_api.route('/updateCourseVideoCount', methods=['POST'])
@jwt_required()
def updateCourseVideoCount():

    current_user = get_jwt_identity()
    if not current_user:
        return jsonify(ret_data(UNAUTHORIZED_ACCESS))

    phone = current_user['register_phone']

    count = request.form.get('video_count', None)

    courseid = request.form.get('courseid', None)

    if not courseid:
        return jsonify(ret_data(PARAMS_ERROR))

    if count:
        user_course = User_Course.query.filter_by(phone=phone,courseid=courseid).first()
        user_course.video_count = int(count)
        db.session.commit()
        return jsonify(ret_data(SUCCESS, data='该课程视频观看次数修改成功！'))

    return jsonify(ret_data(SUCCESS, data='该课程视频观看次数修改成功！'))


#web端添加用户课程视频次数信息 20240130 xiaojuzi v2
@web_back_api.route('/addCourseVideoCount', methods=['POST'])
@jwt_required()
def addCourseVideoCount():

    current_user = get_jwt_identity()
    if not current_user:
        return jsonify(ret_data(UNAUTHORIZED_ACCESS))

    phone = current_user['register_phone']

    count = request.form.get('video_count', None)

    courseid = request.form.get('courseid', None)

    if not courseid or not count:
        return jsonify(ret_data(PARAMS_ERROR))


    user_course = User_Course.query.filter_by(phone=phone, courseid=courseid).first()

    if user_course:
        return jsonify(ret_data(PARAMS_ERROR, data='该课程视频次数权限已存在，请直接修改！'))

    user_course = User_Course(phone=phone, courseid=courseid, video_count=int(count))
    db.session.add(user_course)
    db.session.commit()

    return jsonify(ret_data(SUCCESS, data='该课程视频观看次数添加成功！'))

#web端用户播放课程视频次数减少 20240131 xiaojuzi v2
@web_back_api.route('/updateCourseVideoByCourseId', methods=['POST'])
@jwt_required()
def updateCourseVideoByCourseId():

    current_user = get_jwt_identity()

    if not current_user:
        return jsonify(ret_data(UNAUTHORIZED_ACCESS))

    phone = current_user['register_phone']

    courseid = request.form.get('courseid', None)

    if not courseid:
        return jsonify(ret_data(PARAMS_ERROR))

    user_course = User_Course.query.filter_by(phone=phone, courseid=courseid).first()
    user_course.video_count -= 1

    db.session.commit()

    return jsonify(ret_data(SUCCESS, data='该课程视频观看次数减少成功！'))


#获取所有图片分类 20240229 xiaojuzi v2
@web_back_api.route('/getAllPictureCategory', methods=['POST'])
@jwt_required()
def getAllPictureCategory():

    current_user = get_jwt_identity()

    if not current_user:
        return jsonify(ret_data(UNAUTHORIZED_ACCESS))

    option_url = ADMIN_HOST + f"/poem/imageType/getAll"
    logging.info('getAllPictureCategory发送的option_url：%s ' % option_url)

    response = requests.post(option_url,json={},timeout=10)
    # 检查请求是否成功
    if response.status_code == 200:

        data = response.json()

        return jsonify(ret_data(SUCCESS, data=data['data']))
    else:
        return jsonify(ret_data(JSON_ERROR, data=response.status_code))



#获取所有图片 20240229 xiaojuzi v2
@web_back_api.route('/getAllPicture', methods=['POST'])
@jwt_required()
def getAllPicture():
    current_user = get_jwt_identity()

    if not current_user:
        return jsonify(ret_data(UNAUTHORIZED_ACCESS))

    number = request.form.get('pageIndex', None)

    page_size = request.form.get('pageSize', None)

    createTimeStart = request.form.get('createTimeStart', None)

    createTimeEnd = request.form.get('createTimeEnd', None)

    name = request.form.get('name', None)

    imageTypeId = request.form.get('imageTypeId', None)

    direction = request.form.get('direction', None)

    option_url = ADMIN_HOST + f"/poem/image/page"

    json = {
        'pageIndex':number,
        'page_size':page_size,
        'createTimeStart':createTimeStart,
        'createTimeEnd':createTimeEnd,
        'name':name,
        'imageTypeId':imageTypeId,
        'direction':direction
    }

    logging.info('getAllPicture发送的option_url：%s ' % option_url)

    response = requests.post(option_url,json=json,timeout=10)

    # 检查请求是否成功
    if response.status_code == 200:
        data = response.json()
        return jsonify(ret_data(SUCCESS, data=data['data']))
    else:
        return jsonify(ret_data(JSON_ERROR, data=response.status_code))


#web端对场景下设备进行运行控制 20240313 xiaojuzi v2
@web_back_api.route('/push_action', methods=['POST'])
@jwt_required()
def videoAutoPushActionToDevice():

    current_user = get_jwt_identity()
    if not current_user:
        return jsonify(ret_data(UNAUTHORIZED_ACCESS))

    operate = request.form.get('operate', 3)

    sceneid = request.form.get('sceneid')

    if not sceneid:
        return jsonify(ret_data(PARAMS_ERROR))

    openid = current_user['openid']

    sceneid = json.loads(sceneid)

    device_list = getDeviceListBySceneId(sceneid)

    if not device_list:
        return jsonify(ret_data(DEVICE_NOT_FIND))

    for device in device_list:
        push_json = {
            'type': 3,
            'deviceid': device.deviceid,
            'fromuser': openid,
            'message': {
                'operate': operate
            }
        }

        logging.info(push_json)

        errcode = send_message(push_json)

        logging.info('push_action发送的result：%s ' % errcode)

    return jsonify(ret_data(SUCCESS))










