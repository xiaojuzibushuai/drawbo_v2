import asyncio
import random
import string

from utils import Sample

#阿里云同步发消息 xiaojuziv2 20231128
def send_sms(phone_numbers: str, sign_name: str, template_code: str, code: str) -> dict:

    response = Sample.Sample.send_sms(phone_numbers, sign_name, template_code, code)

    return response

#阿里云异步发消息 xiaojuziv2 20231128
def send_sms_async(phone_numbers: str, sign_name: str, template_code: str, code: str) -> dict:

    response = asyncio.run(Sample.Sample.send_sms_async(phone_numbers, sign_name, template_code, code))

    return response

def generate_verification_code():

    characters = string.digits
    verification_code = ''.join(random.choice(characters) for _ in range(4))
    return verification_code

if __name__ == '__main__':
    #18771111506 18707281085
    phone_numbers='18771111506'

    SignName='画小宇'
    # SignName='画小宇小程序'
    #画小宇正式小程序密码重置验证 SMS_464035626
    #画小宇正式小程序登录注册验证 SMS_464040703
    #画小宇测试小程序密码重置验证 SMS_464050656
    #画小宇测试小程序登录注册验证 SMS_464120632
    TemplateCode='SMS_464040703'

    # code = '341211'

    code = generate_verification_code()

    # response = send_sms(phone_numbers,SignName, TemplateCode,code)

    response = send_sms_async(phone_numbers, SignName, TemplateCode, code)

    print(response)
