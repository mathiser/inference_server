import docker
import atexit
import functools
import logging
import shutil
import tempfile
import threading
import time
import zipfile
from file_handling import *
from api_calls import *
from init_rabbit import rabbit_channel

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

    # Get task context from DB
    logging.info(f"[ ]{uid}: Requesting task context from DB")
    task = get_task_by_uid(uid)
    logging.info(f"[X]{uid}: Requesting task context from DB")

    logging.info(f"[ ]{uid}: Task: {task}")
    logging.info(f"[ ]{uid}: ")

    # Get model_context
    logging.info(f"[ ]{uid}: Requesting model context from DB")
    model = get_model_by_id(task['model_id'])
    logging.info(f"[X]{uid}: Requesting model context from DB")

    # Set an input and output folder in /tmp/ for container
    input_folder = os.path.join("/tmp/", task["uid"], "input")
    output_folder = os.path.join("/tmp/", task["uid"], "output")

    # Request get image_zip from DB
    logging.info(f"[ ]{uid}: Requesting input_zip from DB")
    res = get_input_by_id(task["id"])
    logging.info(f"[X]{uid}: Requesting input_zip from DB")

    logging.info(f"[ ]{uid}: Unzipping input_zip to {input_folder}")
    unzip_response_to_location(res, input_folder)
    logging.info(f"[X]{uid}: Unzipping input_zip to {input_folder}")

    ############ LONG RUNNING JOB ###############
    kw = {}
    kw["image"] = model["container_tag"]
    kw["command"] = None ## Already default, but for explicity
    kw["ipc_mode"] = "host" ## Full access to ram

    # Set input, output and model volumes // see https://docker-py.readthedocs.io/en/stable/containers.html
    kw["volumes"] = {}
    kw["volumes"][input_folder] = {"bind": model["input_mountpoint"], "mode": "ro"}
    kw["volumes"][output_folder] = {"bind": model["output_mountpoint"], "mode": "rw"}

    if model["model_available"]:
        kw["volumes"][model["model_volume"]] = {"bind": model["model_mountpoint"], "mode": "ro"}

    if model["use_gpu"]:
        kw["device_requests"] = [docker.types.DeviceRequest(count=-1, capabilities=[['gpu']])]

    logging.info(f"[ ]{uid}: Running container job")
    cli = docker.from_env()
    cli.containers.run(**kw)
    ############ END OF LONG RUNNING JOB ###############


    # Zip the output_folder into payload_zip and save in /tmp/{uid}.zip
    tmp_output_zip = zip_folder_to_tmpfile(output_folder)
    logging.info(f"[X]{uid}: Zipping {output_folder}")

    # Post output_zip to DB/output
    logging.info(f"[ ]{uid}: Posting output to DB")
    res = post_output_by_uid(uid, tmp_output_zip)

    if res.ok:
        logging.info(f"[X]{uid}: Posting {tmp_output_zip} to DB")
        cb = functools.partial(ack_message, channel, delivery_tag, uid)
        connection.add_callback_threadsafe(cb)
    else:
        logging.error("Error in posting output zip to DB")

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

    on_message_callback = functools.partial(on_message, args=(rabbit_connection, threads))
    rabbit_channel.basic_consume(queue=os.environ["UNFINISHED_JOB_QUEUE"], on_message_callback=on_message_callback)

    logging.info(' [*] Waiting for messages')
    exit_func = functools.partial(on_exit, threads, rabbit_connection)
    atexit.register(on_exit)
    rabbit_channel.start_consuming()

