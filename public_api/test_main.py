import os
import shutil

from private_api.message_queue.tests.test_mq_rabbit_impl import TestMessageQueueRabbitMQImpl

os.environ["TZ"] = "Europe/Copenhagen"
os.environ["API_HOSTNAME"] = "private_api"
os.environ["API_PORT"] = "7000"
os.environ["API_URL"] = "http://private_api:7000"
os.environ["LOG_LEVEL"] = "10"

os.environ["DATA_DIR"] = ".tmpdata"
os.environ["API_TASKS"] = "/api/tasks/"

os.environ["API_OUTPUT_ZIPS"] = "/api/tasks/outputs/"
os.environ["API_INPUT_ZIPS"] = "/api/tasks/inputs/"
os.environ["API_MODELS"] = "/api/models/"
os.environ["API_MODELS_BY_HUMAN_READABLE_ID"] = "/api/models/human_readable_id/"
os.environ["API_MODEL_ZIPS"] = "/api/models/zips/"
os.environ["RABBIT_HOSTNAME"] = "rabbit"
os.environ["RABBIT_PORT"] = "5672"

import unittest
from main import *


class TestFastAPIImpl(unittest.TestCase):
    """
    This is a testing of functions in api/img/api/private_fastapi_impl.py
    """
    def setUp(self) -> None:
        self.mq_tests = TestMessageQueueRabbitMQImpl(port=5672)
        self.mq_tests.setUp()
        self.mq = self.mq_tests.mq_client

    def tearDown(self) -> None:
        self.mq_tests.tearDown()
        shutil.rmtree(os.environ.get("DATA_DIR"))

    def test_main(self):
        main()

if __name__ == '__main__':
    unittest.main()
