import logging
import os
os.environ["RABBIT_DOCKER_TAG"] = "rabbitmq:3.9.17"
os.environ["LOG_LEVEL"] = "80"
os.environ["UNFINISHED_JOB_QUEUE"] = "unfinished_job_queue"
os.environ["FINISHED_JOB_QUEUE"] = "finished_job_queue"

import threading
import unittest

import docker

from database.tests.test_db_sqlite_impl import TestSQLiteImpl
from message_queue.rabbit_mq_impl import MQRabbitImpl

PORT_NO = 5672

class TestMessageQueueRabbitMQImpl(unittest.TestCase):
    """
    This is a tests of functions in api/img/message_queue/rabbit_mq_impl.py
    """

    def get_port(self):
        global PORT_NO
        PORT_NO += 1
        return PORT_NO

    def make_mq_container(self):
        cli = docker.from_env()
        self.RABBIT_PORT = self.get_port()
        self.take_down_mq_container(str(self.RABBIT_PORT))

        self.RABBIT_HOSTNAME = "localhost"

        cli.images.pull(os.environ.get("RABBIT_DOCKER_TAG"))
        print(f"Spinning up RabbitMQ with name {str(self.RABBIT_PORT)}")

        cli.containers.run(os.environ.get("RABBIT_DOCKER_TAG"),
                           name=str(self.RABBIT_PORT),
                           hostname=self.RABBIT_HOSTNAME,
                           ports={5672: self.RABBIT_PORT},
                           detach=True)
        cli.close()

    @staticmethod
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


    def setUp(self) -> None:
        self.base_dir = ".tmp"
        self.mq_client = None
        self.db_tests = TestSQLiteImpl()
        self.db_tests.setUp()
        self.make_mq_container()
        self.mq_client = MQRabbitImpl(host=self.RABBIT_HOSTNAME,
                                      port=self.RABBIT_PORT,
                                      unfinished_queue_name=os.environ["UNFINISHED_JOB_QUEUE"],
                                      finished_queue_name=os.environ["FINISHED_JOB_QUEUE"])

    def tearDown(self) -> None:
        self.db_tests.tearDown()
        self.mq_client.close(*self.mq_client.get_connection_and_channel())
        self.take_down_mq_container(self.take_down_mq_container(str(self.RABBIT_PORT)))
        #t = threading.Thread(target=self.take_down_mq_container, kwargs={"name": str(self.RABBIT_PORT)})
        #t.start()

    def test_get_connection_and_channel(self):
        self.conn, self.chan = self.mq_client.get_connection_and_channel()
        self.assertTrue(self.conn.is_open)
        self.assertTrue(self.chan.is_open)
        return self.conn, self.chan

    def test_publish_unfinished(self):
        task = self.db_tests.test_post_task_intended()
        self.mq_client.publish_unfinished_task(task)
        conn, chan = self.mq_client.get_connection_and_channel()
        method_frame, header_frame, body = chan.basic_get(self.mq_client.unfinished_queue_name)
        self.assertEqual(body.decode(), task.uid)
        chan.basic_ack(method_frame.delivery_tag)
        self.mq_client.close(conn, chan)

    def test_publish_finished(self):
        task = self.db_tests.test_post_task_intended()
        self.mq_client.publish_finished_task(task)

        conn, chan = self.mq_client.get_connection_and_channel()
        method_frame, header_frame, body = chan.basic_get(self.mq_client.finished_queue_name)

        self.assertEqual(body.decode(), task.uid)
        chan.basic_ack(method_frame.delivery_tag)
        self.mq_client.close(conn, chan)

if __name__ == '__main__':
    unittest.main()
