import json
import os
import time
from datetime import datetime, timedelta

import requests
from flask import request, jsonify, Blueprint
import logging

from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import func, Integer, cast

from config import HOST, ADMIN_HOST
from models.course import Course, DeviceCourse
from models.device import Device
from models.key_board_data import KeyBoardData
from models.parent_game import ParentGame
from models.user import User
from models.user_device import User_Device
from script.mosquitto_product import send_message, send_external_message
from sys_utils import db
from utils.image_convert.convert_image_to_dat import convert_image_to_dat, convert_camera_image_to_dat, \
    test_convert_image_to_dat
from utils.tools import ret_data, decorator_sign, create_noncestr
from utils.error_code import *

from pypinyin import pinyin, Style

from models.user_external_device import UserExternalDevice


#mqtt小程序调用设备
mqtt_api = Blueprint('mqtt', __name__, url_prefix='/api/v1/mqtt')

#  本代码为v2版本 xiaojuzi  记录2023920

@mqtt_api.route('/voice', methods=['POST'])
@jwt_required()
# @decorator_sign
def mqtt_push_voice():
    """
    语音对讲 xiaojuzi v2
    fromuser: 消息来源ID，微信openid/后台
    url: 资源地址(包含后缀)
    category: =0： 实时  =1： 留言
    :return: json
    """
    current_user = get_jwt_identity()
    if not current_user:
        return jsonify(ret_data(UNAUTHORIZED_ACCESS))

    openid = request.form.get('openid', None)
    url = request.form.get('url', None)
    category = request.form.get('category', 0)

    logging.info('openid: %s, url: %s, category:%s' % (openid, url, category))
    if not openid or not url:
        return jsonify(ret_data(PARAMS_ERROR))

    # xiaojuzi

    push_json = {
        'type': 0,
        'fromuser': openid,
        'deviceid': '',
        'message': {
            'url': url,
            'category': category
        }
    }

    # xiaojuzi
    device_list = sortDeviceByMaster(openid)

    if not device_list:
        return jsonify(ret_data(DEVICE_NOT_FIND))

    for device in device_list:

        push_json['deviceid'] = device.deviceid

        logging.info(push_json)

        errcode = send_message(push_json)

    return jsonify(ret_data(errcode))


@mqtt_api.route('/music', methods=['POST'])
@jwt_required()
# @decorator_sign
def mqtt_push_music():
    """
    音乐/故事 xiaojuzi v2
    openid: 消息来源ID，微信openid/后台
    operate: =0:  stop
             =1:  play
             =2:  pause
             =4:  resume
    url: 资源地址(包含后缀)
    category: =0： 音乐  =1： 故事
    :return: json
    """
    current_user = get_jwt_identity()
    if not current_user:
        return jsonify(ret_data(UNAUTHORIZED_ACCESS))

    openid = request.form.get('openid', None)
    operate = request.form.get('operate', 0)
    url = request.form.get('url', None)
    category = request.form.get('category', 0)

    logging.info('openid: %s, operate: %s, url: %s, category:%s' % (openid, operate, url, category))

    if not openid or not url:
        return jsonify(ret_data(PARAMS_ERROR))
    arg = url.split('/').pop()

    push_json = {
        'type': 1,
        'fromuser': openid,
        'deviceid': '',
        'message': {
            'operate': operate,
            'arg': arg,
            'url': url,
            'category': category
        }
    }

    # xiaojuzi
    device_list = sortDeviceByMaster(openid)

    if not device_list:
        return jsonify(ret_data(DEVICE_NOT_FIND))

    for device in device_list:
        push_json['deviceid'] = device.deviceid

        logging.info(push_json)
        errcode = send_message(push_json)

    return jsonify(ret_data(errcode))

@mqtt_api.route('/data', methods=['POST'])
@jwt_required()
# @decorator_sign
def mqtt_push_data() -> object:
    """
    数据文件 xiaojuzi v2
    openid: 消息来源ID，微信openid/后台
    course_id: 课程id
    is_free: 是否免费 1 免费 0 不免费
    :return:
    """
    current_user = get_jwt_identity()
    if not current_user:
        return jsonify(ret_data(UNAUTHORIZED_ACCESS))

    openid = request.form.get('openid', None)
    course_id = request.form.get('course_id', None)
    is_free = request.form.get('is_free', '0')

    logging.info('openid: %s, course_id: %s, is_free: %s' % (openid, course_id, is_free))
    if not openid or not course_id:
        return jsonify(ret_data(PARAMS_ERROR))

    if course_id == 'null':
        course_id = None

    #根据多设备管理选中的设备进行数据推送 xiaojuzi 2023919

    #查询用户已经选择的设备id

    device_list = sortDeviceByMaster(openid)

    if not device_list:
        return jsonify(ret_data(DEVICE_NOT_FIND))

    #新增发消息等待20231021
    count = 0

    for device in device_list:
        if is_free == '1':

            # 免费试用
            course = Course.query.get(int(course_id))

            if not course:
                return jsonify(ret_data(SYSTEM_ERROR))

            arg = course.save_path
            # 更新设备当前课程
            device.course_name = 'free'  # 免费课程
            device.course_id = int(course_id)

            # db.session.commit()

        else:
            # 判断次数
            device_course = DeviceCourse.query.filter_by(device_id=device.id, course_id=int(course_id)).first()

            if not device_course:
                return jsonify(ret_data(SYSTEM_ERROR))

            if device_course.use_count:
                arg = device_course.course.save_path

                # 使用次数减1
                device_course.use_count = device_course.use_count - 1

                # db.session.commit()

                # 更新设备当前课程
                device.course_name = device_course.course.title
                device.course_id = int(course_id)

                # db.session.commit()
            else:

                #20231010 更新 xiaojuzi
                data = '设备名为：'+device.devicename+'\n没有使用次数'

                return jsonify(ret_data(NOT_USE_COUNT,data=data))

        push_json = {
            'type': 2,
            'deviceid': device.deviceid,
            'fromuser': openid,
            'message': {
                'arg': arg,
                'url': HOST + '/upload/' + arg
                }
        }

        logging.info(push_json)

        errcode = send_message(push_json)

        # 新增发消息等待20231107 xiaojuzi
        # if count < 5:
        #     errcode = send_message(push_json)
        #     count += 1
        # else:
        #     time.sleep(1)
        #     errcode = send_message(push_json)
        #     count = 0

    db.session.commit()

    return jsonify(ret_data(errcode))


@mqtt_api.route('/newGetKeyboardDataImpl', methods=['GET','POST'])
#xiaojuzi 20231121 外部接口 返回给前端键盘答题数据  数据面板(新)
def newGetKeyboardDataImpl():

    date_format = '%Y-%m-%d %H:%M:%S'

    #xiaojuzi  v2 更新 多条件查询
    # start_time = request.form.get('start_time',datetime.now().strftime(date_format))
    # end_time = request.form.get('end_time',datetime.now().strftime(date_format))

    #20231125 v2 临时更改
    start_time = request.args.get('start_time',None)
    end_time = request.args.get('end_time',None)

    if not start_time or not end_time:
        start_time = datetime.now().strftime(date_format)
        end_time = datetime.now().strftime(date_format)

    page_size =request.form.get('page_size',0)
    page_number =request.form.get('page_number',0)

    page_size = int(page_size)
    page_number = int(page_number)

    start_time = datetime.strptime(start_time, date_format)
    end_time = datetime.strptime(end_time, date_format)

    query_time = int((end_time - start_time).total_seconds())

            #SELECT COUNT( parentid ) AS total_count,parent_game.id AS parentid,parent_game.game_name AS parentname,
            #key_board_data.id,key_board_data.devicename,key_board_data.gametype,key_board_data.answer,
            #SUM( key_board_data.answer = 1 ) AS correct_count,SUM( key_board_data.answer = 0 ) AS incorrect_count
            #FROM
             #parent_game
             #JOIN key_board_data ON parent_game.id = key_board_data.parentid
         #GROUP BY
             #parentid,
             #key_board_data.devicename,
             #key_board_data.gametype;

    # 0 为正确 1为错误
    if query_time > 0:

        #20231120 xiaojuzi v2
        query = db.session.query(
            # func.count(ParentGame.id).label('total_count'),
            ParentGame.id.label('parentid'),
            ParentGame.game_name.label('parentname'),
            KeyBoardData.id,
            KeyBoardData.devicename,
            KeyBoardData.gametype,
            KeyBoardData.answer,
            cast(func.sum(KeyBoardData.answer == '0'), Integer).label('correct_count'),
            cast(func.sum(KeyBoardData.answer == '1'), Integer).label('incorrect_count')
        ).join(
            ParentGame,
            ParentGame.id == KeyBoardData.parentid
        ).filter(
            KeyBoardData.status_update > start_time , KeyBoardData.status_update < end_time
        ).group_by(
            ParentGame.id,
            KeyBoardData.devicename,
            KeyBoardData.gametype
        )

        results = query.all()

        total_count = len(results)

        if total_count < 0:
            return jsonify({
                'errcode': SUCCESS,
                'total_count': 0,
                'data': None
            })

    else:
        #20231120 xiaojuzi v2

        query = db.session.query(
            # func.count(ParentGame.id).label('total_count'),
            ParentGame.id.label('parentid'),
            ParentGame.game_name.label('parentname'),
            KeyBoardData.id,
            KeyBoardData.devicename,
            KeyBoardData.gametype,
            KeyBoardData.answer,
            cast(func.sum(KeyBoardData.answer == '0'), Integer).label('correct_count'),
            cast(func.sum(KeyBoardData.answer == '1'), Integer).label('incorrect_count')
        ).join(
            ParentGame,
            ParentGame.id == KeyBoardData.parentid
        ).group_by(
            ParentGame.id,
            KeyBoardData.devicename,
            KeyBoardData.gametype
        )

        results = query.all()

        total_count = len(results)

        if total_count < 0:
            return jsonify({
                'errcode': SUCCESS,
                'total_count': 0,
                'data': None
            })

        # 暂时删除
        # total_pages = (total_count + page_size - 1) // page_size
        #
        # # 校验页码
        # if page_number < 1 or page_number > total_pages:
        #     raise ValueError("Invalid page number")
        #
        # results = query.limit(page_size).offset((page_number - 1) * page_size).all()


    #执行学情分析表的数据集的筛选过滤 分页返回数据
    data_list = getKeyboardProcessData(results)

    if page_size > 0 and page_number > 0:

        #对数据分页
        select_data_list = paginate_data(data_list,page_size, page_number)

        return jsonify({
            'errcode': SUCCESS,
            'total_count': len(data_list),
            'data': select_data_list
        })
    else:
        return jsonify({
            'errcode': SUCCESS,
            'total_count': len(data_list),
            'data': data_list
        })


#20231121 xiaojuzi v2 预置课学情分析表 数据处理方法 返回需要的格式数据
def getKeyboardProcessData(results: list) -> list:

    # 符合条件的游戏数据
    data_list = []

    # 初始化
    child_dict = {
        'gametype': '',
        'answer': '',
        'accuracy': '',
        'correct_count': '',
        'incorrect_count': ''
    }

    device_dict = {
        'parentid': '',
        'parentname': '',
        'child_list': []
    }

    data_dict = {
        'id': '',
        'devicename': '',
        'device_list': []
    }


    for d in results:

        data_dict['id'] = d.id
        data_dict['devicename'] = d.devicename

        device_dict['parentid'] = d.parentid
        device_dict['parentname'] = d.parentname

        child_dict['gametype'] = d.gametype
        child_dict['answer'] = d.answer
        child_dict['correct_count'] = d.correct_count
        child_dict['incorrect_count'] = d.incorrect_count

        if d.correct_count != 0:
            child_dict['accuracy'] = round(d.correct_count / (d.correct_count + d.correct_count), 4)

        #进行初始化判断
        if len(data_list) == 0:
            device_dict['child_list'].append(child_dict)
            data_dict['device_list'].append(device_dict)
            data_list.append(data_dict)

        else:
            flag = False  # 标记是否找到相同小游戏的记录
            #如果data_list里面有相同设备的记录则直接添加进去
            for da in data_list:
                if d.devicename == da['devicename']:
                    for de in da['device_list']:
                        if de['parentid'] == d.parentid:
                            de['child_list'].append(child_dict)
                            flag = True
                            break

                    if not flag:
                        device_dict['child_list'].append(child_dict)
                        da['device_list'].append(device_dict)

                    break

            #与for同级 for循环完后执行
            else:
                device_dict['child_list'].append(child_dict)
                data_dict['device_list'].append(device_dict)
                data_list.append(data_dict)

        # 初始化
        child_dict = {
            'gametype': '',
            'answer': '',
            'accuracy': '',
            'correct_count': '',
            'incorrect_count': ''
        }

        device_dict = {
            'parentid': '',
            'parentname': '',
            'child_list': []
        }

        data_dict = {
            'id': '',
            'devicename': '',
            'device_list': []
        }

    return data_list

#分页方法 xiaojuzi 20231121 v2
def paginate_data(data, page_size, page_number) -> list:

    total_items = len(data)

    #整除运算符 得到正确的总页数
    total_pages = (total_items + page_size - 1) // page_size

    # 校验每页大小
    if page_size < 1:
        raise ValueError("Invalid page size")

    # 校验页码
    if page_number < 1 or page_number > total_pages:
        raise ValueError("Invalid page number")

    start_index = (page_number - 1) * page_size
    end_index = start_index + page_size
    paginated_data = data[start_index:end_index]

    return paginated_data


@mqtt_api.route('/getKeyboardDataImpl', methods=['GET','POST'])
#xiaojuzi 20231031 外部接口 返回给前端键盘答题数据  数据面板（旧）
def getKeyboardDataImpl():

    date_format = '%Y-%m-%d %H:%M:%S'

    #xiaojuzi updateby20231117 v2 更新 多条件查询
    # start_time = request.form.get('start_time',start_time= datetime.now().strftime(date_format))
    # end_time = request.form.get('end_time',end_time= datetime.now().strftime(date_format))

    start_time = request.args.get('start_time',datetime.now().strftime(date_format))
    end_time = request.args.get('end_time',datetime.now().strftime(date_format))

    if not start_time or not end_time:
        start_time = datetime.now().strftime(date_format)
        end_time = datetime.now().strftime(date_format)

    start_time = datetime.strptime(start_time, date_format)
    end_time = datetime.strptime(end_time, date_format)

    query_time = int((end_time - start_time).total_seconds())

    data_list = []

    # 初始化
    data_dict = {
        'id': '',
        'devicename': '',
        'gametype': '',
        'accuracy': '',
        'correct_count': '',
        'incorrect_count': ''
    }

    # SELECT k.devicename,k.gametype,SUM(k.answer = 1) AS correct_count,SUM(k.answer = 0) AS incorrect_count
    #     FROM  key_board_data k
    #     GROUP BY
    #     k.devicename,
    #     k.gametype;
    # 0 为正确 1为错误
    if query_time > 0:

        results = db.session.query(KeyBoardData.id,KeyBoardData.devicename,KeyBoardData.gametype,
                                  cast(func.sum(KeyBoardData.answer == '0'),Integer).label('correct_count'),
                                  cast(func.sum(KeyBoardData.answer == '1'),Integer).label('incorrect_count')
        ).filter(
            KeyBoardData.status_update > start_time , KeyBoardData.status_update < end_time
        ).group_by(
            KeyBoardData.devicename,
            KeyBoardData.gametype
        ).all()

    else:
        results = db.session.query(KeyBoardData.id,KeyBoardData.devicename,KeyBoardData.gametype,
                                  cast(func.sum(KeyBoardData.answer == '0'),Integer).label('correct_count'),
                                  cast(func.sum(KeyBoardData.answer == '1'),Integer).label('incorrect_count')
        ).group_by(
            KeyBoardData.devicename,
            KeyBoardData.gametype
        ).all()


    for d in results:

        data_dict['id'] = d.id
        data_dict['devicename'] = d.devicename
        data_dict['correct_count'] = d.correct_count
        data_dict['incorrect_count'] = d.incorrect_count
        data_dict['accuracy'] = 0
        data_dict['gametype'] = 0

        if d.gametype.startswith("0"):
            data_dict['gametype'] = d.gametype[1:]

        if d.correct_count != 0:
            data_dict['accuracy'] = round(d.correct_count / (d.correct_count + d.correct_count), 4)

        data_list.append(data_dict)

        data_dict = {
            'id': '',
            'devicename': '',
            'gametype': '',
            'accuracy': '',
            'correct_count': '',
            'incorrect_count': ''
        }

    if data_list:
        return jsonify(ret_data(SUCCESS, data=data_list))

    return jsonify(ret_data(SUCCESS,data=None))

# @mqtt_api.route('/mqttPushAnswerToKeyBoard', methods=['POST'])
# xiaojuzi 20231030 给键盘推送数据
def mqttPushAnswerToKeyBoard(gametype :str,answer :str,parentid: str,courseid=None):

    logging.info(' gametype: %s , answer: %s ,parentid: %s ,courseid %s' % (gametype, answer,parentid,courseid))

    if not gametype or not answer or not parentid:
        return jsonify(ret_data(PARAMS_ERROR))

    topic = '/keyboard/answer/'

    #20231121 xiaojuzi v2 数据面板修改游戏类型
    push_json = f"-{parentid}-{gametype}{answer}-{courseid}"

    logging.info("游戏类型及其答案更新：" + push_json)

    errcode = send_external_message(push_json,topic)

    return jsonify(ret_data(errcode))


@mqtt_api.route('/mqttPushCustomPictureDataImpl', methods=['POST'])
#封装实现 外部接口 非小程序接口 xiaojuzi 20231027 白板画画传到画小宇设备上画画
def mqttPushCustomPictureDataImpl():

    #获取图像
    file = request.files.get('file')

    deviceid = request.form.get('deviceid')

    if not file or not deviceid:

        return jsonify(ret_data(PARAMS_ERROR))

    deviceid = deviceid.replace(":", "")

    #获取文件名
    file_name = file.filename

    static_folder = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),'static').replace('\\', '/')

    # file_dir = create_noncestr(8)
    file_dir = file_name.split('.')[0]

    #要保存的文件的文件夹
    save_file_floder = static_folder + f'/custompicture/{file_dir}'

    save_file_png = save_file_floder + f'/{file_name}'

    save_file_svg = save_file_floder + f'/{file_dir}.svg'

    save_file_gcode =save_file_floder + f'/{file_dir}.gcode'

    save_file_dat =save_file_floder + f'/{file_dir}.dat'

    #生成lrc文件
    init_lrc_file = file_dir + '.lrc'

    # 生成dat文件
    init_dat_file = file_dir + '.dat'

    lrc_data = '000000000000000000000000000000000'

    device = UserExternalDevice.query.filter_by(deviceid=deviceid).all()

    if not device:
        return jsonify(ret_data(UNBIND_DEVICE))

    #修改逻辑 只允许一个投影绑定一个画小宇设备 不允许绑定多个先 xiaojuzi20231108
    for de in device:

        if de.external_deviceid:

            #延时保存文件 20231108
            try:
                # 文件夹不存在则创建
                if not os.path.exists(save_file_floder):
                    os.makedirs(save_file_floder)

                file.save(save_file_png)

                # 创建lrc文件
                initAutoPictureFile(save_file_floder, init_lrc_file, lrc_data)

                # 图像转为dat文件
                convert_image_to_dat(save_file_png, save_file_svg, save_file_gcode, save_file_dat)

            except Exception as e:
                print("文件保存或转换失败:", str(e))

            result = mqttPushCustomPictureData(de.userid,de.external_deviceid,file_dir)

            return jsonify(ret_data(result))

    return jsonify(ret_data(UNBIND_DEVICE))


@mqtt_api.route('/mqttPushCameraPictureDataImpl', methods=['POST'])
#封装实现 外部接口 非小程序接口 xiaojuzi 20231115 摄像头拍照画画传到画小宇设备上画画 dengshuibin
def mqttPushCameraPictureDataImpl():

    #获取图像二进制文件 硬件要求这样传输
    data = request.data

    # head = request.headers

    deviceid = request.headers.get('deviceid')

    # print(deviceid)

    if not data or not deviceid:

        return jsonify(ret_data(PARAMS_ERROR))

    deviceid = deviceid.replace(":", "")
    logging.info('临时解析出mac地址：'+deviceid)

    #生成文件名
    # file_dir = create_noncestr(8)
    #文件名格式修改 20231216
    temp = str(int(time.time())) + create_noncestr(4)
    temp1 = str(datetime.now().year) + '/' + str(datetime.now().month)
    file_dir = temp1 + "/" + temp

    file_name = temp

    static_folder = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),'static').replace('\\', '/')


    #要保存的文件的文件夹
    save_file_floder = static_folder + f'/camerapicture/{file_dir}'

    save_file_png = save_file_floder + f'/{file_name}.png'

    save_file_svg = save_file_floder + f'/{file_name}.svg'

    save_file_gcode =save_file_floder + f'/{file_name}.gcode'

    save_file_dat =save_file_floder + f'/{file_name}.dat'

    #生成lrc文件
    init_lrc_file = file_name + '.lrc'

    # 生成dat文件
    # init_dat_file = file_dir + '.dat'

    lrc_data = '000000000000000000000000000000000'

    device = UserExternalDevice.query.filter_by(deviceid=deviceid).all()

    if not device:
        return jsonify(ret_data(UNBIND_DEVICE))

    #修改逻辑 只允许一个投影绑定一个画小宇设备 不允许绑定多个先 xiaojuzi20231108
    for de in device:

        if de.external_deviceid:

            #延时保存文件 20231108
            try:
                # 文件夹不存在则创建
                if not os.path.exists(save_file_floder):
                    os.makedirs(save_file_floder)

                with open(save_file_png,'wb') as file:
                    file.write(data)

                # file.save(save_file_png)

                # 创建lrc文件
                initAutoPictureFile(save_file_floder, init_lrc_file, lrc_data)

                # 图像转为dat文件 20231118 xiaojuzi
                convert_camera_image_to_dat(save_file_png, save_file_svg, save_file_gcode, save_file_dat)

            except Exception as e:
                print("文件保存或转换失败:", str(e))

            result = mqttPushCameraPictureData(de.userid,de.external_deviceid,temp1,temp)

            return jsonify(ret_data(result))

    return jsonify(ret_data(UNBIND_DEVICE))

@mqtt_api.route('/mqttPushKeyImage', methods=['POST'])
#封装实现 外部接口 非小程序接口 xiaojuzi 20231115 按键获取后台dat传到画小宇设备上画画 dengshuibin
def mqttPushKeyImage():

    deviceid = request.headers.get('deviceid')
    courseid = request.headers.get('courseid')
    number = request.headers.get('number')

    if not deviceid or not courseid or not number:

        return jsonify(ret_data(PARAMS_ERROR))

    deviceid = deviceid.replace(":", "")
    logging.info('临时解析出mac地址：'+deviceid)

    #生成文件名
    # file_dir = create_noncestr(8)
    temp = str(int(time.time())) + create_noncestr(4)
    temp1 = str(datetime.now().year) + '/' + str(datetime.now().month)
    file_dir = temp1 + "/" + temp

    file_name = temp

    static_folder = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),'static').replace('\\', '/')

    # file_dir = create_noncestr(8)
    # file_dir = file_name.split('.')[0]

    #要保存的文件的文件夹
    save_file_floder = static_folder + f'/keyboard/{file_dir}'

    save_file_dat =save_file_floder + f'/{file_name}.dat'

    #生成lrc文件
    init_lrc_file = file_name + '.lrc'

    # 生成dat文件
    # init_dat_file = file_dir + '.dat'

    lrc_data = '000000000000000000000000000000000'

    logging.info('drawbo:' + os.getenv('drawbo'))
    device = UserExternalDevice.query.filter_by(deviceid=deviceid).all()
    logging.info('device' + str(len(device)))

    if not device:
        return jsonify(ret_data(UNBIND_DEVICE))

    #修改逻辑 只允许一个投影绑定一个画小宇设备 不允许绑定多个先 xiaojuzi20231108
    for de in device:

        if de.external_deviceid:

            #延时保存文件 20231108
            try:
                # 文件夹不存在则创建
                if not os.path.exists(save_file_floder):
                    os.makedirs(save_file_floder)

                option_url = ADMIN_HOST+f"/poem/option/getOption?courseId={courseid}&number={number}"
                getOptionAndDownload(option_url,save_file_dat)

                # 创建lrc文件
                initAutoPictureFile(save_file_floder, init_lrc_file, lrc_data)

            except Exception as e:
                print("文件保存或转换失败:", str(e))

            result = mqttPushKeyBoardPictureData(de.userid,de.external_deviceid,temp1,temp)

            return jsonify(ret_data(result))

    return jsonify(ret_data(UNBIND_DEVICE))

@mqtt_api.route('/testMqttPushFacePictureDataImpl', methods=['POST'])
#封装实现 外部接口 小程序接口 xiaojuzi 20231120 人脸上传让机器画人脸 临时测试接口
def testMqttPushFacePictureDataImpl():

    # 获取图像
    file = request.files.get('file')

    #获取用户选择的设备 20240102 xiaojuzi
    deviceid = request.form.get('deviceid',None)
    openid = request.form.get('openid', None)
    rotate = request.form.get('rotate', None)

    #临时给三个
    deviceid = '8c000c6d6004c991e52'
    openid = 'oN3gn5BKNImmh6ZFA5YDFmbwlDcc'
    # rotate = 2

    if not file or not openid:
        return jsonify(ret_data(PARAMS_ERROR))

    device = Device.query.filter_by(deviceid=deviceid).first()

    if not device:
        return jsonify(ret_data(DEVICE_NOT_FIND))

    # 获取文件名
    file_name = file.filename

    static_folder = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'static').replace('\\',
                                                                                                                '/')
    # file_dir = create_noncestr(8)
    file_dir = file_name.split('.')[0][:8]
    file_name = file_name[:8]

    # 要保存的文件的文件夹
    save_file_floder = static_folder + f'/test/{file_dir}'

    save_file_png = save_file_floder + f'/{file_name}.jpg'

    save_file_svg = save_file_floder + f'/{file_dir}.svg'

    save_file_gcode = save_file_floder + f'/{file_dir}.gcode'

    save_file_dat = save_file_floder + f'/{file_dir}.dat'

    # 生成lrc文件
    init_lrc_file = file_dir + '.lrc'

    # 生成dat文件
    init_dat_file = file_dir + '.dat'

    lrc_data = '000000000000000000000000000000000'

    try:
        # 文件夹不存在则创建
        if not os.path.exists(save_file_floder):
            os.makedirs(save_file_floder)

        file.save(save_file_png)

        # 创建lrc文件
        initAutoPictureFile(save_file_floder, init_lrc_file, lrc_data)

        #20240102 xiaojuzi v2 rotate 旋转角度
        # 图像转为dat文件
        test_convert_image_to_dat(rotate,save_file_png, save_file_svg, save_file_gcode, save_file_dat)


    except Exception as e:
        print("文件保存或转换失败:", str(e))

    # return jsonify(ret_data(SUCCESS))
    #TODO 待修改为自动选择哪台设备画人像 20240102
    result = mqttPushFacePictureDataImpl(openid,deviceid, file_dir)

    return jsonify(ret_data(result))

@mqtt_api.route('/testMqttPushGirlDataImpl', methods=['POST'])
#临时接口小女孩骑自行车dat xiaojuzi 20231207
def testMqttPushGirlDataImpl():

    arg = 'girl'

    push_json = {
        'type': 2,
        'deviceid': '8c000c6d6004c9221d2',
        'fromuser': 'oN3gn5BKNImmh6ZFA5YDFmbwlDcc',
        'message': {
            # arg为文件夹名字  xiaojuzi 20231120
            'arg': arg,
            'url': HOST + '/test/' + arg
        }
    }

    errcode = send_message(push_json)

    return errcode

@mqtt_api.route('/test1MqttPushGirlDataImpl', methods=['POST'])
#临时接口小女孩吃鸡腿dat xiaojuzi 20231207
def test1MqttPushGirlDataImpl():

    arg = 'girl1'

    push_json = {
        'type': 2,
        'deviceid': '8c000c6d6004c9221d2',
        'fromuser': 'oN3gn5BKNImmh6ZFA5YDFmbwlDcc',
        'message': {
            # arg为文件夹名字  xiaojuzi 20231120
            'arg': arg,
            'url': HOST + '/test/' + arg
        }
    }

    errcode = send_message(push_json)

    return errcode


#创建初始化lrc文件 xiaojuzi 20231027
def initAutoPictureFile(folder_path, file_name, data):
    # 创建文件夹
    # os.makedirs(folder_path, exist_ok=True)

    # 构造文件路径
    file_path = os.path.join(folder_path, file_name)

    try:
        # 写入数据
        with open(file_path, 'w') as file:
            file.write(data)
    except Exception as e:
        print("默认文件初始化失败:", str(e))


#下载用户白板画画的png生成的dat文件 20231026 xiaojuzi v2  注意：要自己生成一个为0的lrc文件不然机器执行会报错
def mqttPushCustomPictureData(openid: str,deviceid: str,arg: str):

    """
    数据文件 xiaojuzi v2
    openid: 消息来源ID，微信openid/后台
    deviceid: 设备id
    :return:
    """

    logging.info('openid: %s, deviceid: %s, arg: %s' % (openid, deviceid,arg))

    if not openid or not deviceid or not arg:
        return jsonify(ret_data(PARAMS_ERROR))

    push_json = {
        'type': 2,
        'deviceid': deviceid,
        'fromuser': openid,
        'message': {
            #arg为文件夹名字  xiaojuzi 20231026
            'arg': arg,
            'url': HOST + '/custompicture/' + arg
        }
    }

    logging.info(push_json)

    errcode = send_message(push_json)

    return errcode

#下载用户摄像头画画的图片生成的dat文件 20231110 xiaojuzi v2  注意：要自己生成一个为0的lrc文件不然机器执行会报错 dengshuibin
def mqttPushCameraPictureData(openid: str,deviceid: str,arg: str,temp=None):

    """
    数据文件 xiaojuzi v2
    openid: 消息来源ID，微信openid/后台
    deviceid: 设备id
    :return:
    """

    logging.info('openid: %s, deviceid: %s, arg: %s' % (openid, deviceid,arg))

    if not openid or not deviceid or not arg:
        return jsonify(ret_data(PARAMS_ERROR))

    push_json = {
        'type': 2,
        'deviceid': deviceid,
        'fromuser': openid,
        'message': {
            #arg为文件夹名字  xiaojuzi 20231110
            'arg': temp,
            'url': HOST + '/camerapicture/' + arg + '/' + temp
        }
    }

    logging.info(push_json)

    errcode = send_message(push_json)

    return errcode

def mqttPushKeyBoardPictureData(openid: str,deviceid: str,arg: str,temp=None):

    """
    数据文件 xiaojuzi v2
    openid: 消息来源ID，微信openid/后台
    deviceid: 设备id
    :return:
    """

    logging.info('openid: %s, deviceid: %s, arg: %s' % (openid, deviceid,arg))

    if not openid or not deviceid or not arg:
        return jsonify(ret_data(PARAMS_ERROR))

    push_json = {
        'type': 2,
        'deviceid': deviceid,
        'fromuser': openid,
        'message': {
            #arg为文件夹名字  xiaojuzi 20231110
            'arg': temp,
            'url': HOST + '/keyboard/' + arg + '/' + temp
        }
    }

    logging.info(push_json)

    errcode = send_message(push_json)

    return errcode

#下载上传的人脸转换数据 临时测试 20231120 xiaojuzi v2  注意：要自己生成一个为0的lrc文件不然机器执行会报错
def mqttPushFacePictureDataImpl(openid: str,deviceid: str,arg: str):

    """
    数据文件 xiaojuzi v2
    openid: 消息来源ID，微信openid/后台
    deviceid: 设备id
    :return:
    """

    logging.info('openid: %s, deviceid: %s, arg: %s' % (openid, deviceid,arg))

    if not openid or not deviceid or not arg:
        return jsonify(ret_data(PARAMS_ERROR))

    push_json = {
        'type': 2,
        'deviceid': deviceid,
        'fromuser': openid,
        'message': {
            #arg为文件夹名字  xiaojuzi 20231120
            'arg': arg,
            'url': HOST + '/test/' + arg
        }
    }

    logging.info(push_json)

    errcode = send_message(push_json)

    return errcode

#下载上传的人脸转换数据 临时测试 20231120 xiaojuzi v2  注意：要自己生成一个为0的lrc文件不然机器执行会报错
def mqttPushFacePictureDataImpl(openid: str,deviceid: str,arg: str):

    """
    数据文件 xiaojuzi v2
    openid: 消息来源ID，微信openid/后台
    deviceid: 设备id
    :return:
    """

    logging.info('openid: %s, deviceid: %s, arg: %s' % (openid, deviceid,arg))

    if not openid or not deviceid or not arg:
        return jsonify(ret_data(PARAMS_ERROR))

    push_json = {
        'type': 2,
        'deviceid': deviceid,
        'fromuser': openid,
        'message': {
            #arg为文件夹名字  xiaojuzi 20231120
            'arg': arg,
            'url': HOST + '/test/' + arg
        }
    }

    logging.info(push_json)

    errcode = send_message(push_json)

    return errcode

#下载唤醒词数据 xiaojuzi 2023928
def mqtt_push_wakeword_data(openid :str,deviceid :str,wakeword :str) -> object:
    """
    数据文件 xiaojuzi v2
    openid: 消息来源ID，微信openid/后台
    deviceid: 设备id
    :return:
    """
    logging.info('openid: %s, deviceid: %s' % (openid, deviceid))

    if not openid or not deviceid:
        return jsonify(ret_data(PARAMS_ERROR))

    wakeword_pinyin = _convert_to_pinyin(wakeword)

    push_json = {
        'type': 7,  # 7为下载唤醒词类型 xiaojuzi v2
        'deviceid': deviceid,
        'fromuser': openid,
        'message': {
            'arg': wakeword_pinyin,
            'url': HOST + '/wakeword/' + wakeword_pinyin
        }
    }

    logging.info(push_json)

    errcode = send_message(push_json)

    return errcode


#中文转拼音方法 xiaojuzi 2023928
def _convert_to_pinyin(chinese):
    pinyin_list = pinyin(chinese, style=Style.NORMAL)
    pinyin_str = ''.join([item[0] for item in pinyin_list])
    return pinyin_str


@mqtt_api.route('/action', methods=['POST'])
@jwt_required()
# @decorator_sign
def mqtt_push_action():
    """
    运行控制 xiaojuzi v2
    openid: 消息来源ID，微信openid/后台
    operate: =1:  play
             =2:  pause
             =3:  exit
             =4:  power off
             =5:  get status
    :return: json
    """
    current_user = get_jwt_identity()
    if not current_user:
        return jsonify(ret_data(UNAUTHORIZED_ACCESS))

    openid = request.form.get('openid', None)
    operate = request.form.get('operate', None)
    # xiaojuzi v2
    deviceid = request.form.get('deviceid', None)

    logging.info('openid: %s, operate: %s' % (openid, operate))
    if not openid or not operate:
        return jsonify(ret_data(PARAMS_ERROR))

    push_json = {
        'type': 3,
        'deviceid': deviceid,
        'fromuser': openid,
        'message': {
            'operate': operate
        }
    }

    # xiaojuzi查询用户已经选择的设备

    device_list = sortDeviceByMaster(openid)

    count = 0

    if not device_list:
        return jsonify(ret_data(DEVICE_NOT_FIND))

    for device in device_list:

        push_json['deviceid'] = device.deviceid

        #不是主设备给静音 暂时删除 20231107 占用通道 废弃先
        # if device.is_master:
        #     if device.volume < 75:
        #         device.volume = 70
        #         _mqtt_push_volume(openid,device.deviceid,device.volume)
        # else:
        #     if device.volume > 25:
        #         device.volume = 0
        #         _mqtt_push_volume(openid,device.deviceid,device.volume)

        logging.info(push_json)

        errcode = send_message(push_json)

        # 新增发消息等待20231107 xiaojuzi
        # if count < 5:
        #     errcode = send_message(push_json)
        #     count += 1
        # else:
        #     time.sleep(0.1)
        #     errcode = send_message(push_json)
        #     count = 0

    db.session.commit()

    return jsonify(ret_data(errcode))


#内部方法 不提供接口功能 xiaojuzi 批量调整设备横版竖版 20231114
def get_mqtt_push_direction(openid :str,deviceids :list,direction :str):

    # 18为设备未找到
    errcode = 18

    for deviceid in deviceids:

        device1 = Device.query.filter_by(deviceid=deviceid).first()

        device = User_Device.query.filter_by(userid=openid, deviceid=deviceid).first()

        if device:
            if (device.is_choose == True) & (
                    int(datetime.now().timestamp()) - device1.status_update.timestamp() <= 30):
                #20231130 需求更改 xiaojuzi v2
                if int(direction) == 1:

                    device1.direction = 0
                else:
                    device1.direction = 1

                # 发送消息
                push_json = {'type': 8,
                             'fromuser': openid,
                             'deviceid': deviceid,
                             'direction': device1.direction
                             }

                logging.info(push_json)

                errcode = send_message(push_json)

    # 没报错在提交
    db.session.commit()

    return errcode

'''
 xiaojuzi v2 20231114
 控制设备横竖版mqtt接口
'''
@mqtt_api.route('/mqtt_push_direction', methods=['POST'])
@jwt_required()
# @decorator_sign
def mqtt_push_direction():
    current_user = get_jwt_identity()
    if not current_user:
        return jsonify(ret_data(UNAUTHORIZED_ACCESS))

    openid = request.form.get('openid', None)
    deviceid = request.form.get('deviceid', None)
    direction = request.form.get('direction', None)

    if not openid or not deviceid or not direction:
        return jsonify(ret_data(PARAMS_ERROR))

    device1 = Device.query.filter_by(deviceid=deviceid).first()

    device = User_Device.query.filter_by(userid=openid, deviceid=deviceid).first()

    if device:
        if (device.is_choose == True) & (
                int(datetime.now().timestamp()) - device1.status_update.timestamp() <= 30):

            # 20231130 需求更改 xiaojuzi v2
            if int(direction) == 1:

                device1.direction = 0
            else:
                device1.direction = 1

            #发送消息
            push_json = {'type': 8,
                         'fromuser': openid,
                         'deviceid': deviceid,
                         'direction': direction
                         }

            logging.info(push_json)

            errcode = send_message(push_json)

            db.session.commit()

            return jsonify(ret_data(errcode))

        return jsonify(ret_data(SUCCESS, data="设备未选择或未在线"))

    return jsonify(ret_data(UNBIND_DEVICE))


#内部方法 不提供接口功能 xiaojuzi 调整音量 20231114
def get_mqtt_push_volume(openid :str,deviceids :list,volume :int):

    # 18为设备未找到
    errcode = 18

    for deviceid in deviceids:

        device1 = Device.query.filter_by(deviceid=deviceid).first()

        device = User_Device.query.filter_by(userid=openid, deviceid=deviceid).first()

        if device:
            if (device.is_choose == True) & (
                    int(datetime.now().timestamp()) - device1.status_update.timestamp() <= 30):
                device1.volume = volume

                # 发送消息
                message = {'operate': 2}
                message['arg'] = volume
                push_json = {'type': 4,
                             'fromuser': openid,
                             'deviceid': deviceid,
                             'message': message
                             }

                logging.info(push_json)
                errcode = send_message(push_json)

    # 没报错在提交
    db.session.commit()

    return errcode

'''
 xiaojuzi v2
 控制设备自定义音量mqtt接口
 operate 操作类型 2为自定义音量  0为音量减10  1为音量加10
'''
@mqtt_api.route('/mqtt_push_volume', methods=['POST'])
@jwt_required()
# @decorator_sign
def mqtt_push_volume():

    current_user = get_jwt_identity()
    if not current_user:
        return jsonify(ret_data(UNAUTHORIZED_ACCESS))

    openid = request.form.get('openid', None)
    deviceid = request.form.get('deviceid', None)
    volume = request.form.get('volume', None)

    if not openid or not deviceid or not volume:
        return jsonify(ret_data(PARAMS_ERROR))

    device1 = Device.query.filter_by(deviceid=deviceid).first()

    device = User_Device.query.filter_by(userid=openid, deviceid=deviceid).first()

    if device:
        if (device.is_choose == True) & (
            int(datetime.now().timestamp()) - device1.status_update.timestamp() <= 30):

            device1.volume = volume

            #发送消息
            message = {'operate': 2}
            message['arg'] = volume
            push_json = {'type': 4,
                         'fromuser': openid,
                         'deviceid': deviceid,
                         'message': message
                         }

            logging.info(push_json)
            errcode = send_message(push_json)

            #没报错在提交
            db.session.commit()

            return jsonify(ret_data(errcode))

        return jsonify(ret_data(SUCCESS, data="设备未选择或未在线"))

    return jsonify(ret_data(UNBIND_DEVICE))


@mqtt_api.route('/ui', methods=['POST'])
@jwt_required()
# @decorator_sign
def mqtt_push_ui():
    """
    UI控制 xiaojuzi v2
    openid: 消息来源ID，微信openid/后台
    operate: =0: 音量减
             =1: 音量加
             =2: 音量值
             =3：呼吸灯开
             =4：呼吸灯关
             =5: 恢复模块出厂设置
    arg: Operate=2时的音量具体值  例如50
    :return:
    """

    current_user = get_jwt_identity()
    if not current_user:
        return jsonify(ret_data(UNAUTHORIZED_ACCESS))

    openid = request.form.get('openid', None)
    operate = request.form.get('operate', 0)
    arg = request.form.get('arg', None)

    logging.info('openid: %s, operate: %s, arg: %s' % (openid, operate, arg))
    if not openid:
        return jsonify(ret_data(PARAMS_ERROR))
    message = {'operate': operate}
    count = 0

    if arg:
        message['arg'] = arg

        push_json = {'type': 4,
                     'deviceid': '',
                     'fromuser': openid,
                     'message': message
                     }

        # xiaojuzi查询用户已经选择的设备
        device_list = sortDeviceByMaster(openid)

        if not device_list:
            return jsonify(ret_data(DEVICE_NOT_FIND))

        for device in device_list:

            device.volume = int(arg)

            push_json['deviceid'] = device.deviceid

            logging.info(push_json)

            errcode = send_message(push_json)

            # 新增发消息等待20231107 xiaojuzi
            # if count < 5:
            #     errcode = send_message(push_json)
            #     count += 1
            # else:
            #     time.sleep(0.1)
            #     errcode = send_message(push_json)
            #     count = 0

        db.session.commit()

    return jsonify(ret_data(errcode))


@mqtt_api.route('/sd', methods=['POST'])
# @jwt_required()
@decorator_sign
def mqtt_push_sd():
    """
    SD卡内容控制 xiaojuzi v2
    openid: 消息来源ID，微信openid/后台
    operate: =1：add/replace
             =2： delete
    url: 资源地址(不含后缀)
    :return:
    """
    openid = request.form.get('openid', None)
    operate = request.form.get('operate', None)
    url = request.form.get('url', None)

    #xiaojuzi
    deviceid = request.form.get('deviceid', None)

    logging.info('fromuser: %s, operate: %s, url: %s' % (openid, operate, url))
    if not openid or not operate or not url:
        return jsonify(ret_data(PARAMS_ERROR))
    arg = url.split('/').pop()

    push_json = {
        'type': 5,
        'fromuser': openid,
        'deviceid': deviceid,
        'message': {
            'operate': operate,
            'arg': arg,
            'url': url
        }
    }

    # xiaojuzi
    # 查询用户已经选择的设备id
    device_list = sortDeviceByMaster(openid)

    if not device_list:
        return jsonify(ret_data(DEVICE_NOT_FIND))


    for device in device_list:

        push_json['deviceid'] = device.deviceid

        logging.info(push_json)

        errcode = send_message(push_json)

    return jsonify(ret_data(errcode))

@mqtt_api.route('/upgrade', methods=['POST'])
# @decorator_sign
@jwt_required()
# 固件升级 xiaojuzi
def upgrade():
    """
    固件升级 xiaojuzi v2
    openid: 消息来源ID，微信openid/后台
    :return:
    """
    current_user = get_jwt_identity()
    if not current_user:
        return jsonify(ret_data(UNAUTHORIZED_ACCESS))

    openid = request.form.get('openid', None)
    if not openid:
        return jsonify(ret_data(PARAMS_ERROR))

    push_json = {
        'type': 6,
        'fromuser': openid,
        'deviceid': '',
        'message': {
            'url': '%s/device/test2-fdr' % HOST
        }
    }
    logging.info(push_json)

    count = 0

    #修改的地方 xiaojuzi v2

    device_list = sortDeviceByMaster(openid)

    if not device_list:
        return jsonify(ret_data(DEVICE_NOT_FIND))

    for device in device_list:

        push_json['deviceid'] =device.deviceid

        #1 为true 0为false
        device.is_upgrade = 0

        errcode = send_message(push_json)

        logging.info('固件升级 errcode : %s' % errcode)

        # 新增发消息等待20231107 xiaojuzi
        # if count < 5:
        #     errcode = send_message(push_json)
        #     count += 1
        # else:
        #     time.sleep(0.1)
        #     errcode = send_message(push_json)
        #     count = 0

    db.session.commit()

    return jsonify(ret_data(LATEST_VERSION))


#根据是否设置为主设备给用户选中且在线的设备id排序发送消息
def sortDeviceByMaster(openid: str)-> list:

    user = User.query.filter_by(openid=openid).first()

    if not user:
        return None

    # 查询用户已经绑定的设备id
    devices = User_Device.query.filter_by(userid=openid).all()

    if not devices:
        return None

    device_list = []

    for device in devices:
        device1 = Device.query.filter_by(deviceid=device.deviceid).first()

        if (device.is_choose == True) & (int(datetime.now().timestamp()) - device1.status_update.timestamp() <= 30):
            if device1.is_master:
                device_list.insert(0,device1)
            else:
                device_list.append(device1)

    #按照使用次数排序
    # device_list = sorted(device_list,key=lambda x:x['use_count'], reverse=True)

    return device_list


# 请求接口获取 选项 并 下载 dat dengshuibin
def getOptionAndDownload(url:str,save_path:str):
    logging.info('url: %s' % (url))
    # print('url: %s' % (url))
    response = requests.post(url)

    # 检查请求是否成功
    if response.status_code == 200:
        # 处理返回的数据
        data = response.json()  # 使用 .json() 方法将返回的 JSON 数据转换为 Python 对象
        url = data['data']['url']
        print("dat地址:"+url)  # 输出返回的数据

        response = requests.get(url)

        if response.status_code == 200:
            # 如果请求成功，将文件内容写入本地文件
            with open(save_path, 'wb') as f:
                f.write(response.content)
                print('文件保存成功')
        else:
            print('下载失败，状态码:', response.status_code)

    else:
        print("获取选项接口失败:", response.status_code)