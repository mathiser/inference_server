import os
import time
import unittest

import docker
from docker import errors
from message_queue.rabbit_mq_impl import MQRabbitImpl
from testing.mock_components.mock_db import MockDB
from testing.mock_components.mock_models_and_tasks import MockModelsAndTasks
from dotenv import load_dotenv

load_dotenv(dotenv_path="testing/.env")
cli = docker.from_env()
try:
    container = cli.containers.get(os.environ.get("RABBIT_NAME"))
    container.stop()
    container.remove()
except errors.NotFound as e:
    print(e)

cli.images.pull(os.environ.get("RABBIT_DOCKER_TAG"))
print("Spinning up RabbitMQ")
rabbit_container = cli.containers.run(os.environ.get("RABBIT_DOCKER_TAG"),
                                      name=os.environ.get("RABBIT_NAME"),
                                      hostname=os.environ.get("RABBIT_HOSTNAME"),
                                      ports={os.environ.get("RABBIT_PORT"): os.environ.get("RABBIT_PORT")},
                                      detach=True)

class TestMessageQueueRabbitMQImpl(unittest.TestCase):
    """
    This is a tests of functions in api/img/message_queue/rabbit_mq_impl.py
    """
    def __del__(self):
        try:
            rabbit_container.stop()
            rabbit_container.remove()
            cli.close()
        except Exception as e:
            print(e)

    def setUp(self) -> None:

        self.base_dir = ".tmp"
        self.db = MockDB()
        self.repo = MockModelsAndTasks()
        self.mq_client = None


        counter = 0
        while counter < 60:
            try:
                self.mq_client = MQRabbitImpl(host=os.environ.get("RABBIT_HOSTNAME"), port=int(os.environ.get("RABBIT_PORT")))
                break
            except Exception as e:
                print(e)
                counter += 5
                time.sleep(5)

    def tearDown(self) -> None:
        self.mq_client.close()

    def test_publish_unfinished(self):
        self.mq_client.publish_unfinished_task(self.repo.task)
        method_frame, header_frame, body = self.mq_client.get_from_queue(self.mq_client.unfinished_queue_name)
        self.assertEqual(body.decode(), self.repo.task.uid)
        self.mq_client.ack_method_frame(method_frame)

        self.assertIsNone(self.mq_client.get_from_queue(self.mq_client.unfinished_queue_name))

    def test_publish_finished(self):
        self.mq_client.publish_finished_task(self.repo.task)
        method_frame, header_frame, body = self.mq_client.get_from_queue(self.mq_client.finished_queue_name)
        self.assertEqual(body.decode(), self.repo.task.uid)
        self.mq_client.ack_method_frame(method_frame)

        self.assertIsNone(self.mq_client.get_from_queue(self.mq_client.finished_queue_name))

if __name__ == '__main__':
    unittest.main()
