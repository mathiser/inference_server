import atexit

import pika

rabbit_connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
rabbit_channel = rabbit_connection.channel()

rabbit_channel.queue_declare(queue='container_jobs', durable=True)

# Release connection on exit
atexit.register(rabbit_connection.close)