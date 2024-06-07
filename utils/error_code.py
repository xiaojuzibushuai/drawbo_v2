# -*- coding:utf-8 -*-

SUCCESS = 0
SYSTEM_ERROR = 1
PARAMS_ERROR = 2
TK_NOT_FIND = 3
SIGN_ERROR = 4
SIGN_INVALID = 5
JSON_ERROR = 6
PHONE_NOT_FIND = 7
CODE_NOT_FIND = 8
PHONE_ERROR = 9
CODE_ERROR = 10
LOGIN_ERROR = 11
NOT_USE_COUNT = 12
UNAUTHORIZED_ACCESS = 13
CODE_NOT_EXPIRE = 14
PHONE_IS_USE = 15
PHONE_OR_CODE_ERROR = 16
UNBIND_DEVICE = 17
DEVICE_NOT_FIND = 18
REPEAT_BIND_DEVICE = 19
FILE_NOT_FOUND_ERROR = 20
APIKEY_NOT_EQUAL = 21
USER_NOT_FIND = 22
COURSE_NOT_FIND = 23
FACE_NOT_FIND = 24
DEVICE_IDLE = 128
DEVICE_PLAY = 129
DEVICE_CLOSE = 134
DEVICE_DOWNLOAD = 144
DEVICE_BUSY = 199
DEVICE_EXIST = 200
LATEST_VERSION = 201
COURSE_UNBIND_VIDEO = 202
VIDEO_KEY_NOT_FIND = 203

#xiaojuzi 20231106
QUESTION_NULL = 25
SMS_SEND_FREQUENTLY = 26
SMS_SEND_ERROR = 27
SMS_CODE_ERROR = 28
SMS_CODE_EXPIRE = 29
SMS_CODE_NOT_FIND = 30
PHONE_NUMBER_ERROR = 31
PASSWORD_ERROR = 32
RESET_PASSWORD_ERROR = 33
UPDATE_USER_INFO_ERROR = 34
CANCEL_USER_ACCOUNT_ERROR = 35
SCENE_ERROR = 36
SCENE_SUB_EXIST = 37
SHARE_CODE_ERROR = 38
PHONE_IS_NOT_MATCH = 39
VIDEO_UPLOAD_FAILED = 40
VIDEO_UPLOAD_NAME_REPEATED = 41
VIDEO_FORMAT_ERROR = 42
CHUNK_UPLOAD_EXIST = 43
UNBIND_VIDEO_SCRIPT = 44
VIDEO_UPLOAD_FAST_SUCCESS = 45
VIDEO_IS_PROCESSING = 46
UPDATE_EXTERNAL_ERROR = 47
UPDATE_EXTERNAL_PERMISSION_ERROR = 48
DEVICE_NAME_EXIST = 49
DEVICE_COUNT_EXCEED = 50

ERROR_CODE = {
    SUCCESS: 'success',
    SYSTEM_ERROR: 'system error',
    PARAMS_ERROR: 'params error',
    TK_NOT_FIND: 'tk not find',
    SIGN_ERROR: 'sign error',
    SIGN_INVALID: 'sign invalid',
    JSON_ERROR: 'json error',
    PHONE_NOT_FIND: '手机号未注册',
    CODE_NOT_FIND: '验证码不能为空',
    PHONE_ERROR: '手机号错误',
    CODE_ERROR: '验证码错误',
    LOGIN_ERROR: '用户未登录',
    NOT_USE_COUNT: '没有使用次数',
    UNAUTHORIZED_ACCESS: '未登录',
    CODE_NOT_EXPIRE: '验证码未过期',
    PHONE_IS_USE: '手机号已经登记过',
    PHONE_OR_CODE_ERROR: '手机号或验证码错误',
    UNBIND_DEVICE: '未绑定设备',
    DEVICE_NOT_FIND: '设备不存在或不在线',
    REPEAT_BIND_DEVICE: '重复绑定设备',
    FILE_NOT_FOUND_ERROR: '文件不存在',
    APIKEY_NOT_EQUAL: 'apikey不匹配',
    USER_NOT_FIND: '用户未找到',
    COURSE_NOT_FIND: '课程未找到',
    DEVICE_IDLE: '设备空闲',
    DEVICE_PLAY: '设备正在播放课件',
    DEVICE_CLOSE: '设备已关机',
    DEVICE_DOWNLOAD: '设备正在下载',
    DEVICE_BUSY: '设备繁忙',
    DEVICE_EXIST: '设备已存在',
    FACE_NOT_FIND: '人脸未找到',
    LATEST_VERSION: '已经是最新版本',
    QUESTION_NULL: '课程问题以及答案为空',
    SMS_SEND_FREQUENTLY: '短信发送过于频繁',
    SMS_SEND_ERROR: '短信发送失败',
    SMS_CODE_ERROR: '短信验证码错误',
    SMS_CODE_EXPIRE: '短信验证码过期',
    SMS_CODE_NOT_FIND: '短信验证码未找到',
    PHONE_NUMBER_ERROR: '账号或密码格式错误',
    PASSWORD_ERROR: '账号或密码格式错误',
    RESET_PASSWORD_ERROR: '重置密码失败',
    UPDATE_USER_INFO_ERROR: '更新用户信息失败',
    CANCEL_USER_ACCOUNT_ERROR: '注销用户失败',
    SCENE_ERROR: '场景操作错误',
    SCENE_SUB_EXIST: '小场景已存在',
    SHARE_CODE_ERROR: '分享码失效',
    PHONE_IS_NOT_MATCH: '手机号与当前微信用户不匹配',
    VIDEO_UPLOAD_FAILED: '视频上传失败',
    VIDEO_FORMAT_ERROR: '视频格式错误',
    CHUNK_UPLOAD_EXIST: '分片上传已存在',
    COURSE_UNBIND_VIDEO: '课程未绑定视频',
    VIDEO_KEY_NOT_FIND: '视频key未找到',
    UNBIND_VIDEO_SCRIPT: '未绑定视频脚本',
    VIDEO_UPLOAD_FAST_SUCCESS: '视频秒传成功',
    VIDEO_IS_PROCESSING: '该集数视频正在处理',
    UPDATE_EXTERNAL_ERROR: '更新外设属性失败，请先解绑画小宇',
    UPDATE_EXTERNAL_PERMISSION_ERROR: '更新外设或画小宇属性失败，权限不足',
    DEVICE_NAME_EXIST: '用户下设备名称已存在',
    DEVICE_COUNT_EXCEED: '此用户设备分配次数超过上限',

}
