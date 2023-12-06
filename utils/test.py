import os
from datetime import datetime, date

from sqlalchemy import func

import app
from models import device

import bcrypt

def test():
    code=None

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
    password = '1234567'
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

if __name__ == '__main__':

    test1()
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
