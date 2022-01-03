import atexit
import functools
import json
import logging
import os
import shutil
import threading
import time
import zipfile
from urllib.parse import urljoin

import httpx
import pika
import requests

LOG_FORMAT = ('%(levelname) -10s %(asctime)s %(name) -5s %(funcName) '
              '-5s %(lineno) -d: %(message)s')
LOGGER = logging.getLogger(__name__)

logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)

def ack_message(channel, delivery_tag, uid):
    """Note that `channel` must be the same pika channel instance via which
    the message being ACKed was retrieved (AMQP protocol constraint).
    """
    if channel.is_open:
        logging.info(f"[ ]{uid}: Send acknowledgement to rabbit")
        channel.basic_ack(delivery_tag)
        logging.info(f"[X]{uid}: Send acknowledgement to rabbit")

    else:
        # Channel is already closed, so we can't ACK this message;
        # log and/or do something that makes sense for your app in this case.
        pass
    # Acknowledge that the task was processed


def do_work(connection, channel, delivery_tag, body):
    thread_id = threading.get_ident()
    fmt1: str = 'Thread id: {} Delivery tag: {} Message body: {}'
    LOGGER.info(fmt1.format(thread_id, delivery_tag, body))

    ###################
    # Parse body, which contains the DB id to the task, which shall be run
    uid = body.decode()
    logging.info(" [x] Received %r" % uid)

    # Get task context from DB
    logging.info(f"[ ]{uid}: Requesting task context from DB")
    with httpx.Client() as client:
        res = client.get(urljoin(os.environ["API_URL"], f"tasks/uid/{uid}"))
    logging.info(f"[X]{uid}: Requesting task context from DB")

    task = dict(json.loads(res.content))
    logging.info(f"[ ]{uid}: Task: {task}")
    logging.info(f"[ ]{uid}: ")

    # Set an input and output folder in /tmp/ for container
    input_folder = os.path.join("/tmp/", task["uid"], "input")
    output_folder = os.path.join("/tmp/", task["uid"], "output")
    zip_folder = os.path.join("/tmp/", task["uid"], "zip")
    input_zip = os.path.join(zip_folder, "input.zip")
    output_zip = os.path.join(zip_folder, "output.zip")

    for p in [input_folder, output_folder, zip_folder]:
        if not os.path.exists(p):
            os.makedirs(p)

    # Request get image_zip from DB
    with httpx.Client() as client:
        logging.info(f"[ ]{uid}: Requesting input_zip from DB")
        res = client.get(urljoin(os.environ["API_URL"], f"/inputs/{task['id']}"))
        logging.info(f"[X]{uid}: Requesting input_zip from DB")

        logging.info(f"[ ]{uid}: Wrinting input_zip to {input_zip}")
        # Write res.content to input_zip in tmp
        with open(input_zip, "wb") as f:
            f.write(res.content)
        logging.info(f"[X]{uid}: Wrinting input_zip to {input_zip}")

    logging.info(f"[ ]{uid}: Extracting {input_zip} to {input_folder}")
    # Extract input zipfile to input_folder
    with zipfile.ZipFile(input_zip, "r") as zip:
        zip.extractall(path=input_folder)
    logging.info(f"[X]{uid}: Extracting {input_zip} to {input_folder}")

    logging.info(f"[ ]{uid}: Running container job")
    # Simulate time consuming job
    logging.info(f"Very time consuming task: copy all input files to output_folder and wait 30 sec")
    for f in os.listdir(input_folder):
        shutil.copy(os.path.join(input_folder, f), output_folder)

    toggle = False
    for t in range(30):
        if toggle:
            logging.info(f"[ ]{uid}: {t}: Tik")
        else:
            logging.info(f"[ ]{uid}: {t}: Tok")
        toggle = not toggle
        time.sleep(1)

    # Zip the output_folder into payload_zip and save in /tmp/id.zip
    logging.info(f"[ ]{uid}: Zipping {output_folder} into {output_zip}")
    with zipfile.ZipFile(output_zip, "w") as zip:
        for file in os.listdir(output_folder):
            zip.write(os.path.join(output_folder, file), arcname=file)
    logging.info(f"[X]{uid}: Zipping {output_folder} into {output_zip}")

    # Post output_zip to DB/output
    logging.info(f"[ ]{uid}: Posting {output_zip} to DB")
    with open(output_zip, "rb") as r:
        requests.post(urljoin(os.environ["API_URL"], f"/outputs/{task['id']}"), files={"file": r})
    logging.info(f"[X]{uid}: Posting {output_zip} to DB")

    cb = functools.partial(ack_message, channel, delivery_tag, uid)
    connection.add_callback_threadsafe(cb)

def on_message(channel, method_frame, header_frame, body, args):
    (connection, threads) = args
    delivery_tag = method_frame.delivery_tag
    t = threading.Thread(target=do_work, args=(connection, channel, delivery_tag, body))
    t.start()
    threads.append(t)

def on_exit(threads, connection):
    for thread in threads:
        thread.join()

    connection.close()


if __name__ == '__main__':
    threads = []
    while True:
        try:
            logging.info(f"[ ]: Connecting to rabbit host: {os.environ['RABBIT_HOST']}")
            # Note: sending a short heartbeat to prove that heartbeats are still
            # sent even though the worker simulates long-running work
            rabbit_connection = pika.BlockingConnection(pika.ConnectionParameters(host=os.environ["RABBIT_HOST"], heartbeat=5))
            rabbit_channel = rabbit_connection.channel()
            logging.info(f"[X]: Connecting to rabbit host: {os.environ['RABBIT_HOST']}")

            logging.info(f"[ ]: Declaring queue: {os.environ['UNFINISHED_JOB_QUEUE']} on {os.environ['RABBIT_HOST']}")
            rabbit_channel.queue_declare(queue=os.environ["UNFINISHED_JOB_QUEUE"], durable=True)
            logging.info(f"[ ]: Declaring queue: {os.environ['UNFINISHED_JOB_QUEUE']} on {os.environ['RABBIT_HOST']}")

            prefetch_val = 1
            rabbit_channel.basic_qos(prefetch_count=prefetch_val)
            logging.info(f"[X]: RabbitMQ prefetch_count set to {prefetch_val}")


            on_message_callback = functools.partial(on_message, args=(rabbit_connection, threads))
            rabbit_channel.basic_consume(queue=os.environ["UNFINISHED_JOB_QUEUE"], on_message_callback=on_message_callback)
            break
        except Exception as e:
            logging.error(e)
            logging.error("Failed to connect to RabbitMQ. Timeout 1 sec and try again")
            time.sleep(1)

    logging.info(' [*] Waiting for messages')
    exit_func = functools.partial(on_exit, threads, rabbit_connection)
    atexit.register(on_exit)
    rabbit_channel.start_consuming()

