from dotenv import load_dotenv
from os import getenv, path, makedirs
import datetime
import pika
import json
import sys

load_dotenv()

invoice = """Faktura na przesyłkę %s
Data wystawienia: %s
Cena: %s
Nadawca: %s
Odbiorca: %s"""

RABBITMQ_HOST     = getenv("RABBITMQ_HOST")
RABBITMQ_LOGIN    = getenv("RABBITMQ_LOGIN")
RABBITMQ_PASSWORD = getenv("RABBITMQ_PASSWORD")
RABBITMQ_PORT     = getenv("RABBITMQ_PORT")
RABBITMQ_VH       = getenv("RABBITMQ_VH")

def makeInvoice(data):
    datetime_string = datetime.datetime.now().strftime("%d-%m-%Y-%H-%M-%S")
    filename = datetime_string + "-" + data["id"] + ".txt"
    with open(path.join(invoicedir, filename), "w+", encoding="utf-8") as f:
        f.write(invoice % ( data["id"],
                            datetime_string,
                            data["price"],
                            data["sender"],
                            data["receiver"] ))

currentdir = path.dirname(__file__)
invoicedir = path.join(currentdir, "invoices")
try:
    makedirs(invoicedir)
    print("Stworzono folder \"invoices\"")
except FileExistsError:
    print("Folder \"invoices\" istnieje, nie tworzę nowego")

credentials = pika.PlainCredentials(RABBITMQ_LOGIN, RABBITMQ_PASSWORD)
parameters  = pika.ConnectionParameters(RABBITMQ_HOST, RABBITMQ_PORT, RABBITMQ_VH, credentials)
connection  = pika.BlockingConnection(parameters)
channel = connection.channel()
result = channel.queue_declare(queue='invoices', durable=True)
queue  = result.method.queue

def callback(ch, method, properties, body):
    try:
        data = json.loads(body.decode("utf-8"))
        if "id" not in data or "price" not in data or "sender" not in data or "receiver" not in data:
            raise Exception
        makeInvoice(data)
        print("Stworzono fakturę na przesyłkę " + data["id"])
    except Exception as e:
        print("Błąd w trakcie tworzenia faktury. Dane:")
        print(body)
        print(e)
    ch.basic_ack(delivery_tag=method.delivery_tag, multiple=False)

channel.basic_consume(queue=queue, on_message_callback=callback, auto_ack=False)

if __name__ == '__main__':
    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        sys.exit(0)