from dotenv import load_dotenv
from os import getenv, path, makedirs
import datetime
import pika
import json
import sys

load_dotenv()

RABBITMQ_HOST     = getenv("RABBITMQ_HOST")
RABBITMQ_LOGIN    = getenv("RABBITMQ_LOGIN")
RABBITMQ_PASSWORD = getenv("RABBITMQ_PASSWORD")
RABBITMQ_PORT     = getenv("RABBITMQ_PORT")
RABBITMQ_VH       = getenv("RABBITMQ_VH")

credentials = pika.PlainCredentials(RABBITMQ_LOGIN, RABBITMQ_PASSWORD)
parameters  = pika.ConnectionParameters(RABBITMQ_HOST, RABBITMQ_PORT, RABBITMQ_VH, credentials)
connection  = pika.BlockingConnection(parameters)
channel = connection.channel()
channel.exchange_declare(exchange='logs',
                         exchange_type='topic')
result = channel.queue_declare(queue='', exclusive=True)
queue  = result.method.queue
channel.queue_bind(exchange='logs', queue=queue, routing_key="*.error")

def callback(ch, method, properties, body):
    print(method.routing_key + " " + body.decode("utf-8"))
    ch.basic_ack(delivery_tag=method.delivery_tag, multiple=False)

channel.basic_consume(queue=queue, on_message_callback=callback, auto_ack=False)

if __name__ == '__main__':
    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        sys.exit(0)