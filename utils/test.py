import base64
import json
import multiprocessing
import os
import random
import subprocess
import time
from datetime import datetime, date, timedelta

import qrcode
import requests
from flask import request
from moviepy.video.io.VideoFileClip import VideoFileClip
from sqlalchemy import func

import app
from models import device

import bcrypt


from cryptography.fernet import Fernet
import base64

from models.device import Device
from sys_utils import db


def test():
    code = None

    return False,code

def hash_password(password):
    # 生成盐值
    salt = bcrypt.gensalt()
    # 哈希加密密码
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
    # 返回加密后的密码
    return hashed_password.decode('utf-8')

def check_password(password, hashed_password):
    # 验证密码是否匹配
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))


def test1():
    # 使用示例
    password = 'Aky666666'
    hashed_password = hash_password(password)
    print(hashed_password)
    # hashed_password = '$2b$12$jXWtZ3FGBToGdURVGXa/bOvW4FqJ/TGjuJfR509MxiD/StLrJqcrK'
    # 存储 hashed_password 到数据库中

    # 验证密码
    is_valid = check_password(password, hashed_password)
    if is_valid:
        print("密码正确")
    else:
        print("密码错误")

def get_user_ip():
    try:
        response = requests.get('https://api.ipify.org/?format=json')
        data = response.json()
        # print(data)
        ip_address = data['ip']
        return ip_address
    except requests.exceptions.RequestException as e:
        print("Error:", e)
        return None

def get_location_by_ip(ip):
    url = f'http://ip-api.com/json/{ip}'  # 使用 ip-api.com 的 API
    response = requests.get(url)
    data = response.json()
    if data['status'] == 'success':
        country = data['country']
        city = data['city']
        return f'{city}, {country}'
    else:
        return 'Unknown'

def get_client_ip():
    # 从请求头中获取真实 IP 地址
    x_forwarded_for = request.headers.get('X-Forwarded-For')
    x_real_ip = request.headers.get('X-Real-IP')
    if x_forwarded_for:
        # 由于 X-Forwarded-For 可能包含多个 IP 地址，取第一个
        ip = x_forwarded_for.split(',')[0]
    elif x_real_ip:
        ip = x_real_ip
    else:
        # 如果 X-Forwarded-For 和 X-Real-IP 都不存在，则使用 remote_addr
        ip = request.remote_addr

    # 如果 IP 地址中包含代理服务器的 IP 地址，我们取最后一个 IP 地址
    # 这是为了防止代理服务器伪造 X-Forwarded-For 或 X-Real-IP 字段
    ip = ip.rsplit(':', 1)[-1].strip()

    return ip

def test2():
    # 使用示例
    ip_address = get_user_ip()
    # ip_address = '172.16.0.123'  # 替换为要查询的 IP 地址
    location = get_location_by_ip(ip_address)
    print(location)

def test3():
    ip = '61.235.82.163'
    param = {'ip': ip,
             'json': 'true'}

    url = 'http://whois.pconline.com.cn/ipJson.jsp'
    response = requests.get(url, params=param)
    # print(response.text)

    # print(response.json().get('ip'))
    # print(response.json()['ip'])

    print(response.json())

def test4():

    url = 'http://whois.pconline.com.cn/ipJson.jsp'
    response = requests.get(url, timeout=5)
    data = response.text
    start_index = data.find('"ip":"') + len('"ip":"')
    end_index = data.find('"', start_index)

    if start_index != -1 and end_index != -1:
        ip_address = data[start_index:end_index]
    print(ip_address)

def test5():
    str = 'class1,class2'
    list1 = str.split(",")
    print(list1)

def make_device_qrcode(deviceid: str)->int:
    """
    生成设备二维码 格式 {"type":"share_device","device_id":"123456"} 对象转成base64，在用base64字符串生成二维码
    :param deviceid: 生成二维码字符串
    :return: errcode
    """
    try:
        str_info = '{"type":"share_device","device_id":"%s"}' % deviceid
        b64_byt = base64.b64encode(str_info.encode('utf-8'))
        b64_str = b64_byt.decode('utf-8')
        img = qrcode.make(b64_str)
        with open(os.path.join(os.path.abspath('.'), 'static', 'device', '%s.png' % deviceid), 'wb') as f:
            img.save(f)
    except Exception as e:
        print(e)
def test6():
    deviceid = {'8c000c6d6004c922452','8c000c6d6004c972192', '8c000c6d6004c991e92', '8c000c6d6004c981d52','8c000c6d6004c9223d2','8c000c6d60064842652',
                '8c000c6d600387d1952','8c000c6d6004c931c92','8c000c6d6004c911a92','8c000c6d600506b1e52','8c000c6d6004c992152',
                '8c000c6d600508c2112','8c000c6d600506b2112','8c000c6d6004c961e92','8c000c6d6004c971e52'}
    for d in deviceid:
        code = make_device_qrcode(d)
        print(code)

#20231229 test
def convert_video_to_blob(video_path):
    with open(video_path, 'rb') as file:
        video_data = file.read()
        video_blob = base64.b64encode(video_data)
    return video_blob

def test7():
    devices = [
        {'name': 'Device 1', 'usage_count': 10},
        {'name': 'Device 2', 'usage_count': 5},
        {'name': 'Device 3', 'usage_count': 8},
        {'name': 'Device 4', 'usage_count': 3}
    ]
    sorted_devices = sorted(devices, key=lambda x: x['usage_count'], reverse=True)
    print(sorted_devices)

def test8():
    test_list = []
    for i in range(10):
        if i % 2 == 0:
            test_list.append(0)
        else:
            test_list.append(1)

    print(test_list)

def test9():
    fileMd5 = '032e68f594f292190791658322ab3ed1'
    print(fileMd5.split('-'))
    print(fileMd5.split('-')[0])
    str1 = '123.dat'
    print(str1.split('.')[0])
def test10():
    date_format = '%Y-%m-%d %H:%M:%S'
    expiry_time = (datetime.now() + timedelta(seconds=7 * 24 * 60 * 60)).strftime(date_format)
    print(expiry_time)
    print(type(expiry_time))

def test11():
    dpi_path ='original'
    default_command = [
        'ffmpeg_path',
        '-i', 'video_path',
        '-c:v', 'libx264',  # 对视频编码
        '-c:a', 'acc',  # 对音频编码
        '-s', '640x360',  # 输出视频分辨率
        '-pix_fmt', 'yuv420p',  # 输出视频像素格式
        '-b:a', '128k',  # 音频比特率
        '-b:v', '800k',  # 视频比特率
        '-r', '30',  # 输出视频帧率
        '-hls_key_info_file', 'keyinfo',  # 秘钥文件
        '-f', 'hls',  # 生成hls
        '-hls_time', '5',  # 切片变小
        '-hls_list_size', '0',  # 设置hls播放列表
    ]
    if dpi_path == '360p':
        command = default_command
    elif dpi_path == '480p':
        default_command[8] = '854x480'
        default_command[12] = '128k'
        default_command[14] = '1500k'
    elif dpi_path == '720p':
        default_command[8] = '1280x720'
        default_command[12] = '192k'
        default_command[14] = '2500k'
    elif dpi_path == '1080p':
        default_command[8] = '1920x1080'
        default_command[12] = '192k'
        default_command[14] = '5000k'
    elif dpi_path == 'original':
        default_command[4] = 'copy'
        default_command[6] = 'copy'
        default_command = [default_command[i] for i in range(len(default_command)) if i<7 or i>16]

    print(default_command)

def test12():

    video_data1 = [{"video_base_url": "http://cdn.course.v5ky.com/7/5/7508ef1e417e5b799032131c66e45e93/original", "video_ts_list": 263, "episode": "2", "dpi": "4"}]
    video_data2 =[{"video_base_url": "http://cdn.course.v5ky.com/7/5/7508ef1e417e5b799032131c66e45e93/original", "video_ts_list": 263, "episode": "2", "dpi": "4"},
                 {"video_base_url": "http://cdn.course.v5ky.com/7/5/7508ef1e417e5b799032131c66e45e93/original","video_ts_list": 263, "episode": "2", "dpi": "5"},
           {"video_base_url": "http://cdn.course.v5ky.com/3/8/381a922ba72dedcfaab840d1a19bb300/original", "video_ts_list": 165, "episode": "1", "dpi": "5"}]
    video = [{'video_files':video_data1},{'video_files':video_data2}]
    # sorted_video_data = sorted(video_data, key=lambda x: (int(x['episode']), -int(x['dpi'])))
    for cl in video:
        for data in cl['video_files']:
            if 'video_base_url' in data:
                data['video_base_url'] = data['video_base_url'].replace('cdn.course.v5ky.com',
                                                                        'kaiyu-video-resource.oss-cn-wuhan-lr.aliyuncs.com')

        sorted_video_data = sorted(cl['video_files'], key=lambda x: (int(x['episode']), -int(x['dpi'])))

        cl['video_files'] = sorted_video_data


    print(video)


if __name__ == '__main__':
    # ffmpeg_path = 'D:\\桌面\\ffmpeg\\ffmpeg.exe'
    # print(os.path.dirname(ffmpeg_path))
    # test12()
    deviceid = '8c000c6d6004c972192FFff'
    print(deviceid.upper())
    print(deviceid.lower())
    # topic = 'iot/2/%s' % deviceid + str(int(time.time()))
    # topic1 = "iot/2/%s" % deviceid + str(random.randint(0,100))
    # print(topic)
    # print(topic1)
    # test8()
    # test9()
    # test10()
    # test11()
    # str = '0123'
    # print(str[0:])

    # test7()
    # video_blob =convert_video_to_blob('1.mp4')
    # print(video_blob)

    # url = "https://miniprogram.v5ky.com/test/girl/girl.dat"
    # base_url = "/".join(url.split("/")[:-1])
    # print(base_url)
    # print(url.split("/")[:-1])
    # print(url.split("/"))
    # print(url.split('/')[-2])

    # 生成随机密钥
    # key = Fernet.generate_key()
    # print(key)

    # 创建 Fernet 对象
    # fernet = Fernet('mKKXNLJFBoPzFFiPjMScMuUndgsfcxxwTF1VhkJEmX4=')

    # 要加密的字符串
    # plaintext = 'http://kaiyu-video-resource.oss-cn-wuhan-lr.aliyuncs.com/ygz-1.mp4,http://kaiyu-video-resource.oss-cn-wuhan-lr.aliyuncs.com/ygz-2.mp4'
    # temp = 'gAAAAABljTwtNWqxcK1oipJlUedrIuyX0iDwRoeVppgQOvzqLrdzO8FQ5JFMa3yhuE5W8hye_khokT99ijVdQLrgAsONH0TUwHTYk6TnlEFiKirp0_oBIbLYxoOiOLFj3VNFnq-RLdYr8o2PqJu8AoxGLmu9nAx81UP3iZie7-FC2B2tZ-A0Q6y0YoF1RCj1eZm80dYExc74hrhw3E-iuVNI4MoQZvDeVkXt2kLcUqMHQeydXNkEwgSrgK9ma1UfnYP15dWu1zI9'
    # # 加密字符串
    # # ciphertext = fernet.encrypt(plaintext.encode())
    # ciphertext = video_resource_encrypt(plaintext)
    # # 解密字符串
    # # decrypted_data = fernet.decrypt(ciphertext)
    # decrypted_data = video_resource_decrypt(ciphertext)
    #
    # print("加密后的字符串:", ciphertext.decode())
    # print("解密后的字符串:", decrypted_data.decode())

    # test1()
    # test2()
    # test3()
    # test4()
    # test5()
    # test6()
    # print(os.getcwd())
    # print(os.path.dirname(os.path.abspath(__file__)))
    # print(os.path.abspath(__file__))
    # file_dir = str(datetime.now().year) + '/' + str(datetime.now().month) + "/" + str(int(time.time())) + create_noncestr(4)

    # print(file_dir)
    # print(datetime.now().month)
    # print(os.path.abspath('.'))
    # device.deviceid = '123'
    # device.devicename = 'test2'


    # data = '设备id为：' + device.deviceid + '\n设备名为：' + device.devicename + '\n没有使用次数'
    # print(data)

    # 获取当前脚本文件的绝对路径
    # current_file_path = os.path.abspath(__file__)
    #
    # print("项目绝对路径：", current_file_path)

    # 获取当前脚本文件所在的目录路径（即项目根目录路径）
    # project_root_path = os.path.dirname(current_file_path)
    #
    # print("项目根目录路径：", project_root_path)
    #
    # print(app.static_folder)

    # deviceid = '5E:8D:70:83:65:75'
    # deviceid = deviceid.replace(":","")
    # print(deviceid)

    # str = '2'
    # print(datetime.now().strftime("%Y/%m/%d %H:%M:%S"))

    # 数据列表
    # data_list = []

    # 动态增加数据对象
    # data_list.append(("xiaojuzi", "v2", "20231109"))
    # data_list.append(("xiaojuzi", "v3", "20231110"))

    # print(data_list)
    # print(len(data_list))
    # date_format = '%Y-%m-%d %H:%M:%S'
    # start_time_str = '2023-10-01 13:40:49'
    # end_time_str = '2023-11-19 13:40:49'
    #
    # start_time = datetime.strptime(start_time_str, date_format)
    # end_time = datetime.strptime(end_time_str, date_format)
    #
    # query_time = int((end_time - start_time).total_seconds())
    #
    # print(query_time)

    # today_start_time = datetime.combine(date.today(), datetime.min.time())  # 当天的开始时间
    # today_end_time = datetime.combine(date.today(), datetime.max.time())  # 当天的结束时间
    #
    # print(today_start_time)
    # print(today_end_time)

    # code = 1
    # print('{"code":%s}' % code)
    # response = {'body': {'Message': 'OK', 'RequestId': 'E791A94A-2101-5AE1-836D-D5FF3B3C4D38', 'Code': 'OK', 'BizId': '398912001227585703^0'}, 'headers': {'date': 'Wed, 29 Nov 2023 03:13:06 GMT', 'content-type': 'application/json;charset=utf-8', 'content-length': '110', 'connection': 'keep-alive', 'keep-alive': 'timeout=25', 'access-control-allow-origin': '*', 'access-control-expose-headers': '*', 'x-acs-request-id': 'E791A94A-2101-5AE1-836D-D5FF3B3C4D38', 'x-acs-trace-id': 'f81fbf4899c051aeb88f8b5898d89d5c', 'etag': '1GuG8TOcil6YfXpXQzT731g0'}, 'statusCode': 200}
    # print(response['body']['Code'])

    # file_path = os.path.abspath('.') + os.sep
    # print(os.path.abspath(__file__))
    # print(os.path.abspath('.'))
