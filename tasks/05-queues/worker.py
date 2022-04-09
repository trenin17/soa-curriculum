import pika, sys, os
import json
from bs4 import BeautifulSoup
import requests

def main():
    connection = pika.BlockingConnection(pika.ConnectionParameters('127.0.0.1'))
    channel = connection.channel()

    channel.queue_declare(queue='tasks')

    connection2 = pika.BlockingConnection(pika.ConnectionParameters('127.0.0.1'))
    channel2 = connection2.channel()
    channel2.queue_declare(queue='results')

    def callback(ch, method, properties, body):
        n_query, url = json.loads(body)

        web_page = requests.get(url)
        soup = BeautifulSoup (web_page.text, 'html.parser')
        for link in soup.find_all('a'):
            new_url = str(link.get('href'))
            if (new_url.startswith('/wiki/')):
                new_url = "https://en.wikipedia.org" + new_url
                channel2.basic_publish(exchange='', routing_key='results', body=json.dumps([[n_query, url], [n_query, new_url]]))


    channel.basic_consume(queue='tasks', on_message_callback=callback, auto_ack=True)

    channel.start_consuming()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Interrupted')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)