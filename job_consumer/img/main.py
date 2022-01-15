import atexit
import functools
import threading
import uuid

from api_calls import *
from docker_utils import DockerHandler, DockerVolumeHandler
from file_handling import *
from init_rabbit import rabbit_channel, rabbit_connection
import logging

LOG_FORMAT = ('%(levelname)s:%(asctime)s:%(message)s')
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)

def ack_message(channel, delivery_tag, uid):
    """Note that `channel` must be the same pika channel instance via which
    the message being ACKed was retrieved (AMQP protocol constraint).
    """
    if channel.is_open:
        logging.info(f"{uid}: Send acknowledgement to rabbit")
        channel.basic_ack(delivery_tag)

    else:
        # Channel is already closed, so we can't ACK this message;
        # log and/or do something that makes sense for your app in this case.
        pass
    # Acknowledge that the task was processed


def do_work(connection, channel, delivery_tag, body):
    thread_id = threading.get_ident()
    fmt1: str = 'Thread id: {} Delivery tag: {} Message body: {}'
    logging.info(fmt1.format(thread_id, delivery_tag, body))

    ###################
    # Parse body, which contains the DB id to the task, which shall be run
    uid = body.decode()

    # Get task context from DB
    logging.info(f"{uid}: Requesting task from DB")
    task = get_task_by_uid(uid)
    model = get_model_by_id(task['model_id'])
    logging
    # Set an input and output folder in /tmp/ for container
    with tempfile.TemporaryDirectory() as tmp_dir:

        input_folder = os.path.join(tmp_dir, "input")
        output_folder = os.path.join(tmp_dir, "output")
        for p in [input_folder, output_folder]:
            os.makedirs(p)

        if not DockerVolumeHandler.volume_exists(model["model_volume"]):
            DockerVolumeHandler.create_volume_from_response(get_model_zip_by_id(model["id"]), model["model_volume"])

        if not DockerVolumeHandler.volume_exists(input_folder):
            input_volume_uuid = DockerVolumeHandler.create_volume_from_response(get_input_zip_by_id(task["id"]))

        output_volume_uuid = str(uuid.uuid4()) ## Just assigning a uuid -> on mount do docker container it will be created.

        logging.info(f"input_volume_uuid: {input_volume_uuid}")
        logging.info(f"output_volume_uuid: {output_volume_uuid}")

    # Unzip input to input_folder
    logging.info(f"{uid}: Unzipping input_zip to {input_folder}")
    unzip_response_to_location(get_input_zip_by_id(task["id"]), input_folder)
    logging.info(f"{uid}: Input files: {os.listdir(input_folder)}")

    dh = DockerHandler(input_volume_uuid=input_volume_uuid,
                       output_volume_uuid=output_volume_uuid,
                       task=task,
                       model=model
                       )
    dh.run()

    # Use a helper container to zip output volume and ship to DB
    url = os.environ.get('API_URL') + urljoin(os.environ.get('POST_OUTPUT_ZIP_BY_UID'), task['uid'])
    DockerVolumeHandler.send_volume(volume_uuid=output_volume_uuid, url=url)

    # Delete docker volumes as they are not needed anymore
    DockerVolumeHandler.delete_volume(input_volume_uuid)
    DockerVolumeHandler.delete_volume(output_volume_uuid)

    cb = functools.partial(ack_message, channel, delivery_tag, uid) ## Acknowledgement callback
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

    on_message_callback = functools.partial(on_message, args=(rabbit_connection, threads))
    rabbit_channel.basic_consume(queue=os.environ["UNFINISHED_JOB_QUEUE"], on_message_callback=on_message_callback)

    exit_func = functools.partial(on_exit, threads, rabbit_connection)
    atexit.register(exit_func)

    logging.info(' [*] Waiting for messages')
    rabbit_channel.start_consuming()

