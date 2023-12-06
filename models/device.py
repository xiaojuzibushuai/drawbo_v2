from sys_utils import db
from datetime import datetime


class Device(db.Model):
    """ 设备信息 """
    __tablename__ = 'device'
    id = db.Column(db.Integer, primary_key=True)
    apikey = db.Column(db.String(64), default="")
    deviceid = db.Column(db.String(32), default="")                        # 设备id
    devicename = db.Column(db.String(32), default="")                      # 设备名字 xiaojuzi
    wakeword = db.Column(db.String(256), default="小宇")                 # 唤醒词 xiaojuz
    software_version = db.Column(db.String(8), default="v2")                #版本号  xiaojuzi
    is_master = db.Column(db.Integer, default=0)                            #是否主设备 xiaojuzi
    productid = db.Column(db.String(16), default="")                        # 产品id
    clientid = db.Column(db.String(64), default="")                         # mqtt clientid
    mac = db.Column(db.String(16), default="")                              # mac地址
    remark = db.Column(db.String(64), default="")
    d_type = db.Column(db.Integer, default=0)                               # 类型  第二代主板，此字段为2，否则不上传 add by 20230708
    status = db.Column(db.String(16), default="")                           # 状态
    create_at = db.Column(db.DateTime, default=datetime.now)                # 上线时间
    topic = db.Column(db.String(32), default="iot/2/default_topic")         # 主题
    is_auth = db.Column(db.Integer, default=0)                              # 是否授权
    qrcode_suffix_data = db.Column(db.Text, default="")                     # 设备二维码
    # 设备管理页
    city = db.Column(db.String(16), default="")                             # 城市
    school = db.Column(db.String(64), default="")                           # 学校
    d_class = db.Column(db.String(64), default="")                          # 班级
    phone = db.Column(db.String(64), default="")                            # 管理员电话
    # 设备当前播放的课程
    course_name = db.Column(db.String(64), default="course name")           # 课程
    course_id = db.Column(db.Integer, default=-1)                           # 歌曲id(课程共用)
    menu_id = db.Column(db.Integer, default=-1)                             # 菜单id(以json文件为主，目前为课程菜单)
    menu_course_pointer = db.Column(db.Integer, default=-1)                 # 菜单课程指针
    volume = db.Column(db.Integer, default=0)                               # 音量
    # 更新状态时间
    status_update = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)                  # 更新状态时间
    face_count = db.Column(db.Integer, default=0)                           # 设备检测到的人脸数量
    is_upgrade = db.Column(db.Boolean, default=False)                       # 是否需要升级

    direction = db.Column(db.Integer, default=0)   #0竖版 1横版  xiaojuzi

    def __str__(self):
        return self.deviceid


class QRCodeSerial(db.Model):
    """
    二维码管理
    纸张二维码解析序列号保存
    1、当linux主板解出二维码后是第一种，发送序列包给后台，后台接收到字符串后，同数据库中的已有全球唯一码比对，
    如果数据库中有，返回纸张无效操作包，主板本地播放“纸张无效”语音，否则后台将此全球唯一码加入数据库，并
    返回纸张有效操作包，主板控制眼睛灯闪烁2下。
    2、当linux主板解出二维码后是第二种，发送序列包给后台，后台接收到字符串后，同数据库中的已有全球唯一码比对，
    如果数据库中有，返回纸张无效操作包，主板本地播放“纸张无效”语音，否则后台将此全球唯一码加入数据库，并返
    回纸张有效操作包，主板控制眼睛灯闪烁2下，然后发送课程名称包给后台，开始绘画课程
    """
    __tablename__ = 'qrcode_serial'
    id = db.Column(db.Integer, primary_key=True)
    serial = db.Column(db.String(128), nullable=False)

    def __str__(self):
        return self.id
