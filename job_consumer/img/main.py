import atexit
import functools
import logging
import os
import threading
from urllib.parse import urljoin

from init_rabbit import rabbit_channel, rabbit_connection
from docker_utils import get_task_by_uid, create_volume_from_response, get_input_zip_by_id, \
    create_empty_volume, DockerJobHandler, send_volume, delete_volume, get_model_by_id

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
    model_ids = task["model_ids"]
    logging.info(f"Task: {task}")
    logging.info(f"Model ids: {model_ids}")
    tmp_containers = [] # Used to clean up after job
    input_volume_uuid = create_volume_from_response(get_input_zip_by_id(task["id"]))
    output_volume_uuid = create_empty_volume()
    tmp_containers.append(input_volume_uuid)
    tmp_containers.append(output_volume_uuid)
    logging.info(f"input_volume_uuid: {input_volume_uuid}")
    logging.info(f"output_volume_uuid: {output_volume_uuid}")

    assert(len(model_ids) >= 1)
    if len(model_ids) == 1:
        dh = DockerJobHandler(input_volume_uuid=input_volume_uuid,
                              output_volume_uuid=output_volume_uuid,
                              task_uid=task["uid"],
                              model=get_model_by_id(model_ids[0])
                              )
        dh.run()
        dh.close()

    elif len(model_ids) > 1:
        first = 0
        last = len(model_ids) - 1
        for i, m in enumerate(model_ids):
            model = get_model_by_id(m)
            # Is first but not last
            if i == first and i != last:
                tmp_in_uuid = input_volume_uuid
                tmp_out_uuid = create_empty_volume()
                tmp_containers.append(tmp_out_uuid)
            # Neither first or last
            elif i != first and i != last:
                tmp_in_uuid = tmp_out_uuid
                tmp_out_uuid = create_empty_volume()
                tmp_containers.append(tmp_out_uuid)
            # Is last but not first
            elif i != first and i == last:
                tmp_in_uuid = tmp_out_uuid
                tmp_out_uuid = output_volume_uuid
            else:
                raise Exception("This is not be possible")

            dh = DockerJobHandler(input_volume_uuid=tmp_in_uuid,
                                  output_volume_uuid=tmp_out_uuid,
                                  task_uid=task["uid"],
                                  model=model
                                  )
            dh.run()
            dh.close()


    # Use a helper container to zip output volume and ship to DB
    url = os.environ.get('API_URL') + urljoin(os.environ.get('POST_OUTPUT_ZIP_BY_UID'), task['uid'])
    send_volume(volume_uuid=output_volume_uuid, url=url)

    # Delete docker volumes as they are not needed anymore
    for c in tmp_containers:
        delete_volume(c)

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

