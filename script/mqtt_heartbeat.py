import pika
import json
import os,sys

parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)
from config import MQ_HOST, MQ_PORT, MQ_NAME, MQ_PASSWORD, MQ_QUEUE_NAME

# 配置并连接
user_info = pika.PlainCredentials(MQ_NAME, MQ_PASSWORD)  # 用户名和密码
connection = pika.BlockingConnection(pika.ConnectionParameters(MQ_HOST, MQ_PORT, '/', user_info))  # 连接服务器上的RabbitMQ服务
# 创建一个channel
channel = connection.channel()
# 如果指定的queue不存在，则会创建一个queue，如果已经存在 则不会做其他动作，官方推荐，每次使用时都可以加上这句
channel.queue_declare(queue=MQ_QUEUE_NAME)
push_dict = {
    'topic': 'heartbeat',
    'fromuser': 'system'
}
push_body = str.encode(json.dumps(push_dict))
channel.basic_publish(
        exchange='',  # 当前是一个简单模式，所以这里设置为空字符串就可以了
        routing_key=MQ_QUEUE_NAME,  # 指定消息要发送到哪个queue
        body=push_body  # 指定要发送的消息
    )
connection.close()
