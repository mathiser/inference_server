import io
import json
import os
import zipfile
from urllib.parse import urljoin

import docker
import requests

from init_rabbit import rabbit_channel

def callback(ch, method, properties, body):
    # Parse body, which contains the DB id to the task, which shall be run
    task_id = body.decode()
    print(" [x] Received %r" % task_id)

    # Get task context from DB
    task_context = json.loads(
        requests.get(requests.get(urljoin(os.environ["DB_URL"], f"tasks/{task_id}"))
                     .context)
    )
    # Print response
    print(task_context)

    # Set an input and output folder in /tmp/ for container
    input_folder = os.path.join("/tmp/", task_context.uid, "input")
    output_folder = os.path.join("/tmp/", task_context.uid, "output")

    # Request get image_zip from DB
    input_res = requests.get(requests.get(urljoin(os.environ["DB_URL"], f"inputs/{task_id}")))

    # Dunno if a temp_zip should be made
    #with open("/tmp/input.zip", "wb") as f:
    #    f.write(res.content)

    # Extract uploaded zipfile to input_folder
    with zipfile.ZipFile(io.BytesIO(input_res.content), "r") as zip:
        zip.extractall(path=input_folder)

    # Run container
    docker_client = docker.from_env()

    # Simulate time consuming job
    out_file = os.path.join(output_folder, task_context.uid)
    docker_client.run("ubuntu", f"echo hello-world > {out_file} && sleep 30")

    # Zip the output_folder into payload_zip and save in /tmp/uid.zip
    payload_zip = os.path.join("/tmp/", f"{task_context.uid}.zip")
    with zipfile.ZipFile(payload_zip, "w") as zip:
        for file in os.listdir(output_folder):
            zip.write(os.path.join(output_folder, file), file)

    # Post payload_zip to DB/output
    with open(payload_zip, "rb") as r:
        res = requests.post(urljoin(os.environ["DB_URL"], f"output/{task_id}"), files={"file": r})

    return res

if __name__ == '__main__':
    rabbit_channel.basic_consume(queue='container_jobs', on_message_callback=callback, auto_ack=True)

    print(' [*] Waiting for messages. To exit press CTRL+C')
    rabbit_channel.start_consuming()
