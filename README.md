# RabbitMQSample_LysicsCrawl
基于RabbitMQ实现RPC的应用  
客户端输入网易云音乐歌曲id，服务端爬取歌词返回客户端，客户端打印歌词并保存本地文件  
只支持爬取英文歌词，因为RabbitMQ传递的字符串是bytes格式，返回客户端后无法解析（也可能有解决方案，我本人没有研究出来）
