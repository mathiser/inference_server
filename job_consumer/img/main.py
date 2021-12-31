import time

import docker
import httpx
import json
import logging
import os
import requests
import shutil
import zipfile
from init_rabbit import rabbit_channel
from urllib.parse import urljoin

logging.basicConfig(filename='job-consumer.log', encoding='utf-8', level=logging.INFO)

def callback(ch, method, properties, body):
    # Parse body, which contains the DB id to the task, which shall be run
    task_uid = body.decode()
    print(" [x] Received %r" % task_uid)

    # Get task context from DB
    with httpx.Client() as client:
        res = client.get(urljoin(os.environ["API_URL"], f"tasks/uid/{task_uid}"))

    task = dict(json.loads(res.content))
    print(task)

    # Print response
    print(f"Task context: {task}")

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
        res = client.get(urljoin(os.environ["API_URL"], f"/inputs/{task['id']}"))

        # Write res.content to input_zip in tmp
        with open(input_zip, "wb") as f:
            f.write(res.content)

    # Extract input zipfile to input_folder
    with zipfile.ZipFile(input_zip, "r") as zip:
        zip.extractall(path=input_folder)

    # Run container
    docker_client = docker.from_env()

    # Simulate time consuming job
    print("ubuntu", f"copy input to output && sleep 30")

    for f in os.listdir(input_folder):
        shutil.copy(os.path.join(input_folder, f), output_folder)
    time.sleep(30)


    # Zip the output_folder into payload_zip and save in /tmp/id.zip
    with zipfile.ZipFile(output_zip, "w") as zip:
        for file in os.listdir(output_folder):
            zip.write(os.path.join(output_folder, file), arcname=file)

    # Post output_zip to DB/output
    with open(output_zip, "rb") as r:
        res = requests.post(urljoin(os.environ["API_URL"], f"/outputs/{task['id']}"), files={"file": r})

    # Acknowledge that the task was processed
    ch.basic_ack(delivery_tag=method.delivery_tag)
    return res

if __name__ == '__main__':
    rabbit_channel.basic_consume(queue=os.environ["UNFINISHED_JOB_QUEUE"], on_message_callback=callback)

    print(' [*] Waiting for messages. To exit press CTRL+C')
    rabbit_channel.start_consuming()
