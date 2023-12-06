# 消费者
import json
import pika
import paho.mqtt.client as mqtt
import os,sys
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)
from config import MQ_HOST, MQ_PORT, MQ_NAME, MQ_PASSWORD, MQ_QUEUE_NAME, MQTT_HOST, MQTT_PORT, MQTT_USERNAME, MQTT_PASSWORD, MQTT_CLIENT_ID

# 初始化MQTT
client = mqtt.Client(MQTT_CLIENT_ID)
client.username_pw_set(username=MQTT_USERNAME, password=MQTT_PASSWORD)
client.connect(MQTT_HOST, MQTT_PORT, 3600)
client.loop_start()

# 初始化RabbitMQ
user_info = pika.PlainCredentials(MQ_NAME, MQ_PASSWORD)
connection = pika.BlockingConnection(pika.ConnectionParameters(MQ_HOST, MQ_PORT, '/', user_info))
channel = connection.channel()

# 如果指定的queue不存在，则会创建一个queue，如果已经存在 则不会做其他动作，生产者和消费者都做这一步的好处是
# 这样生产者和消费者就没有必要的先后启动顺序了
channel.queue_declare(queue=MQ_QUEUE_NAME)


# 回调函数
def callback(ch, method, properties, body):
    print('消费者收到:{}'.format(body))
    # 获取topic
    body_dict = json.loads(body)
    topic = body_dict.pop('topic')
    res = client.publish(topic, json.dumps(body_dict), 0)
    print(res)

# channel: 包含channel的一切属性和方法
# method: 包含 consumer_tag, delivery_tag, exchange, redelivered, routing_key
# properties: basic_publish 通过 properties 传入的参数
# body: basic_publish发送的消息


channel.basic_consume(
    queue=MQ_QUEUE_NAME,  # 接收指定queue的消息
    auto_ack=True,  # 指定为True，表示消息接收到后自动给消息发送方回复确认，已收到消息
    on_message_callback=callback  # 设置收到消息的回调函数
)

print('Waiting for messages. To exit press CTRL+C')

# 一直处于等待接收消息的状态，如果没收到消息就一直处于阻塞状态，收到消息就调用上面的回调函数
channel.start_consuming()
