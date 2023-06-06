import logging
import os
import secrets
import threading
import unittest

import docker
import sys

import requests

PORT_NO = 5672
def make_mq_container(port):
    cli = docker.from_env()
    take_down_mq_container(str(port))

    RABBIT_HOSTNAME = "localhost"

    cli.images.pull("rabbitmq")
    print(f"Spinning up RabbitMQ with name {str(port)}")

    cli.containers.run("rabbitmq",
                       name=str(port),
                       hostname=RABBIT_HOSTNAME,
                       ports={5672: port},
                       detach=True)
    cli.close()
def take_down_mq_container(name):
    cli = docker.from_env()
    try:
        logging.info(f"Closing RabbitMQ container with name {name}")
        container = cli.containers.get(name)
        if container:
            container.stop()
            container.remove()
    except Exception as e:
        print(e)
        logging.info(f"Did not find: {name} - which is great!")
    finally:
        cli.close()

class MyTestCase(unittest.TestCase):

    def setUp(self) -> None:
        #make_mq_container(5672)

        os.chdir("./controller")
        from controller.main import Controller
        token = secrets.token_urlsafe(8)
        cont = controller.Controller(INFERENCE_SERVER_TOKEN=token)
        t1 = threading.Thread(target=cont.run)
        t1.start()

        os.chdir("../consumer")
        from consumer.main import Consumer
        cons = consumer.Consumer(INFERENCE_SERVER_TOKEN=token)

        t2 = threading.Thread(target=cons.run)
        t2.start()
    def tearDown(self) -> None:
        pass
        #take_down_mq_container(5672)

    def test_hello_world(self):
        res = requests.get("http://localhost:8123")
        print(res.json())
if __name__ == '__main__':
    unittest.main()
