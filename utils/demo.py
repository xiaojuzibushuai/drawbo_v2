from datetime import datetime, timedelta

from WXBizDataCrypt import WXBizDataCrypt
from api.auth import jwt_redis_blocklist
from models.course import Course
from utils.OSSUploader import list_oss_file
from utils.tools import dict_drop_field


def main():
    appId = 'wx4f4bc4dec97d474b'
    sessionKey = 'tiihtNczf5v6AKRyjwEUhQ=='
    encryptedData = 'CiyLU1Aw2KjvrjMdj8YKliAjtP4gsMZMQmRzooG2xrDcvSnxIMXFufNstNGTyaGS9uT5geRa0W4oTOb1WT7fJlAC+oNPdbB+3hVbJSRgv+4lGOETKUQz6OYStslQ142dNCuabNPGBzlooOmB231qMM85d2/fV6ChevvXvQP8Hkue1poOFtnEtpyxVLW1zAo6/1Xx1COxFvrc2d7UL/lmHInNlxuacJXwu0fjpXfz/YqYzBIBzD6WUfTIF9GRHpOn/Hz7saL8xz+W//FRAUid1OksQaQx4CMs8LOddcQhULW4ucetDf96JcR3g0gfRK4PC7E/r7Z6xNrXd2UIeorGj5Ef7b1pJAYB6Y5anaHqZ9J6nKEBvB4DnNLIVWSgARns/8wR2SiRS7MNACwTyrGvt9ts8p12PKFdlqYTopNHR1Vf7XjfhQlVsAJdNiKdYmYVoKlaRv85IfVunYzO0IKXsyl7JCUjCpoG20f0a04COwfneQAGGwd5oa+T8yO5hzuyDb/XcxxmK01EpqOyuxINew=='
    iv = 'r7BXXKkLb8qrSNn05n0qiA=='

    pc = WXBizDataCrypt(appId, sessionKey)

    data = pc.decrypt(encryptedData, iv)

    print(data)

    new_data = data.copy()

    # data_info = dict_drop_field(data,['watermark'])
    new_data.pop('watermark')

    print(new_data)

    new_data['openid'] = 'o00000000000000000000000000000000'

    print(new_data)

def test1():
   data = list_oss_file()
   
   # jwt_redis_blocklist.hset("iot_notify","123", datetime.now().timestamp)
   # jwt_redis_blocklist.expire("iot_notify",timedelta(days=7))
   



if __name__ == '__main__':
    test1()



    # main()

    # data_list = [
    #     {"userid": 1, "name": "Alice"},
    #     {"userid": 2, "name": "Bob"},
    #     # {"userid": 1, "name": "Charlie"},
    #     # {"userid": 3, "name": "David"},
    #     # {"userid": 2, "name": "Eve"}
    # ]

    # userid = 1
    # data_ids = [da['userid'] for da in data_list ]
    #
    # if userid in data_ids:
    #     print('存在')
    # else:
    #     print('不存在')


    # file_path = 'http://kaiyu-video-resource.oss-cn-wuhan-lr.aliyuncs.com/'
    # print(file_path.split('/')[:-1])
    # folder_path = '/'.join(file_path.split('/')[:-1])
    # print(folder_path)