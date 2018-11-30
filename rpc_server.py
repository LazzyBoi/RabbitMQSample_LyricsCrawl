#coding=utf-8

'''
   rpc_server.py
   ~~~~~~~~~~~~~
   实现RPC的服务端
   对客户端传回的网易云音乐歌曲id，进行歌词爬取并返回客户端
'''

import pika
import requests
import json
import re
import os
from bs4 import BeautifulSoup

# 连接RabbitMQ服务器
connection = pika.BlockingConnection(pika.ConnectionParameters(
        host='localhost'))
channel = connection.channel()

# 生成从客户端传数据到服务端的消息队列rpc queue
channel.queue_declare(queue='rpc_queue')

'''
   对传入的网易云歌曲id进行歌词爬取
   @parm song_id: 网易云歌曲id
   @return lrc: 经过处理的歌词
'''
def get_lyric(song_id):  
    
    url = "http://music.163.com/api/song/lyric?id=" + str(song_id) + "&lv=1&kv=1&tv=-1"

    json_lrc = requests.get(url)
    json_obj = json_lrc.text
    j = json.loads(json_obj)
    initial_lrc = j['lrc']['lyric']
    pat = re.compile(r'\[.*\]')
    lrc = re.sub(pat, '', initial_lrc).strip()

    return lrc

'''
   收到客户端传回的消息，调用处理函数并将结果返回客户端
   @parm ch: 传输channel
   @parm method: 消息队列
   @parm props: 客户端参数
   @parm body: 客户端传回的数据
'''
def on_request(ch, method, props, body):

    song_id = int(body)

    print("服务端获取到的歌曲id是：%s"  % (song_id,))
    response = get_lyric(song_id)

    # 发送消息
    ch.basic_publish(exchange='',
                     routing_key=props.reply_to,  # 调用客户端发来的callback_queue
                     properties=pika.BasicProperties(correlation_id = \
                                                     props.correlation_id),  # 获取客户端唯一的uuid
                     body=str(response))
    ch.basic_ack(delivery_tag = method.delivery_tag)  # 消息确认

channel.basic_qos(prefetch_count=1)  # 为了实现负载均衡，设置一次处理一个消息，处理完之后才会接收下一个消息
channel.basic_consume(on_request, queue='rpc_queue')  # 从rpc_queue队列收到消息后，调用响应函数on_request

print("服务端等待RPC请求...")
channel.start_consuming()