#coding=utf-8

'''
   rpc_client.py
   ~~~~~~~~~~~~~
   实现RPC的客户端
   输入网易云歌曲id，传给服务端，接收服务端传回的歌词，将歌词打印到控制台并保存为本地文件
'''

import pika
import uuid

class RpcClient(object):

    def __init__(self):
        # 连接远程服务端
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(
                host='localhost'))
        self.channel = self.connection.channel()

        result = self.channel.queue_declare(exclusive=True)  # 生成从服务端接收数据的队列
        self.callback_queue = result.method.queue  # 将队列名发给服务端

        self.channel.basic_consume(self.on_response, no_ack=True,
                                   queue=self.callback_queue)  # 收取self.callback_queue队列中的消息，调用on_response函数
    
    '''
       收到消息之后调用
       @parm ch: 传输channel
       @parm method: 消息队列
       @parm props: 客户端参数
       @parm body: 服务端传回的数据
    '''
    def on_response(self, ch, method, props, body):
        # 若服务端传回的id与客户端的id相同，就将服务端传回的body赋给客户端的response
        if self.corr_id == props.correlation_id:
            self.response = body
    
    '''
       向服务端传输数据，并循环收取服务端返回的数据
       @parm song_id: 传给服务端的数据
    '''
    def call(self, song_id):
        
        self.response = None
        self.corr_id = str(uuid.uuid4())  # 随机生成的id，是唯一的
        # 发送消息到rpc_queue
        self.channel.basic_publish(exchange='',
                                   routing_key='rpc_queue',
                                   properties=pika.BasicProperties(
                                         reply_to = self.callback_queue,  # 服务端将结果返回callback_queue
                                         correlation_id = self.corr_id,  # 生成的id发送给服务端
                                         ),
                                   body=str(song_id))
        # 循环收取数据
        while self.response is None:
            self.connection.process_data_events()
        return str(self.response)

'''
   将内容写入文件并存储到本地
   @parm file_name: 文件路径
   @parm contents: 文件内容
'''
def save_to_file(file_name, contents):
    fh = open(file_name, 'w')
    fh.write(contents)
    fh.close

rpc = RpcClient()

id_input = input("请输入网易云歌曲id，为您爬取歌词：")  # 控制台输入歌曲id

response = rpc.call(int(id_input))  # 将消息传给服务端并获取从服务端传回的消息

# 从服务端传回的字符串是bytes形式，需要将b""以及多余的转义符去掉
l = len(response)
lrc = response[2:l-1].replace('\\n', '\n')
lrc = lrc.replace(r'\'', '\'')

print(lrc)  # 控制台打印歌词

# 歌词存储到本地
file_name = str(id_input) + ' lyrics.txt'
save_to_file(file_name, lrc)