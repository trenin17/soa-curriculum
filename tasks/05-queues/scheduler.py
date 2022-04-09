import string
import struct
import pika 
from collections import deque
import json
from threading import Thread, Lock
import os


n_query = 0
mutex = Lock()

class Url:
    query: int
    url: string

    def __init__(self, q, u) -> None:
        self.query = q
        self.url = u

    def ToJson(self) -> bytes:
        return json.dumps([self.query, self.url])
    

urls = deque()
used = set()
parents = {}
queries_in_progress = set([n_query])

url_start = input()
url_end = input()

urls.append(Url(n_query, url_start))

def bfs():
    connection1 = pika.BlockingConnection(
        pika.ConnectionParameters('127.0.0.1'))
    channel1 = connection1.channel()

    channel1.queue_declare(queue='tasks')
    while True:
        mutex.acquire()
        try:
            if len(urls) != 0:
                curr_url = urls[0]
                urls.popleft();
                if curr_url.query in queries_in_progress and curr_url not in used:
                    used.add(curr_url)
                    channel1.basic_publish(exchange='', routing_key='tasks', body=curr_url.ToJson())
        finally:
            mutex.release()
        

bfs_thread = Thread(target = bfs)
bfs_thread.start()

connection2 = pika.BlockingConnection(
    pika.ConnectionParameters('127.0.0.1'))
channel2 = connection2.channel()
channel2.queue_declare(queue='results')

def callback(ch, method, properties, body):
    msg = json.loads(body)
    parent_url = Url(msg[0][0], msg[0][1])
    new_url = Url(msg[1][0], msg[1][1])
    parents[new_url] = parent_url
    mutex.acquire()
    try:
        if new_url.url == url_end:
            queries_in_progress.discard(new_url.query)
            result = []
            while new_url in parents.keys():
                result.append(new_url.url)
                new_url = parents[new_url]
            result.append(new_url.url)
            result.reverse()
            connection2.close()
            os._exit(os.EX_OK)
        else:
            urls.append(new_url)
    finally:
        mutex.release()

channel2.basic_consume(queue='results', on_message_callback=callback, auto_ack=True)
channel2.start_consuming()

