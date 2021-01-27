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

def sendInvoiceToQueue(uuid, price, sender, receiver):
    message = {
        "id" : uuid,
        "price" : price,
        "sender" : sender,
        "receiver" : receiver
    }
    connection  = pika.BlockingConnection(parameters)
    channel = connection.channel()
    channel.queue_declare(queue='invoices', durable=True)
    channel.basic_publish(exchange="", routing_key="invoices", body=json.dumps(message))
    connection.close()