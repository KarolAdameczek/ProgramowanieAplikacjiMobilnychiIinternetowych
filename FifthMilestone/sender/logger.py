from dotenv import load_dotenv
from os import getenv
import datetime
import pika

load_dotenv()

RABBITMQ_HOST     = getenv("RABBITMQ_HOST")
RABBITMQ_LOGIN    = getenv("RABBITMQ_LOGIN")
RABBITMQ_PASSWORD = getenv("RABBITMQ_PASSWORD")
RABBITMQ_PORT     = getenv("RABBITMQ_PORT")
RABBITMQ_VH       = getenv("RABBITMQ_VH")

credentials = pika.PlainCredentials(RABBITMQ_LOGIN, RABBITMQ_PASSWORD)
parameters  = pika.ConnectionParameters(RABBITMQ_HOST, RABBITMQ_PORT, RABBITMQ_VH, credentials)


def log(text, routing_key):
    connection  = pika.BlockingConnection(parameters)

    datetime_string = datetime.datetime.now().strftime("%d-%m-%Y %H-%M-%S")
    log = f"[{datetime_string}] " + text

    channel     = connection.channel()
    channel.exchange_declare(   exchange='logs',
                                exchange_type='topic'   )
    channel.basic_publish(  exchange='logs',
                            routing_key=routing_key,
                            body=log           )
    connection.close()