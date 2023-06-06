import logging
from urllib.parse import urljoin

import requests

from database_client.db_client_interface import DBClientInterface


class DBClientRequestsImpl(DBClientInterface):
    def __init__(self, base_url, x_token, log_level=10):
        LOG_FORMAT = '%(levelname)s:%(asctime)s:%(message)s'
        logging.basicConfig(level=log_level, format=LOG_FORMAT)
        self.logger = logging.getLogger(__name__)
        self.x_token = x_token
        self.base_url = base_url

    def get(self, url, params=None, stream=False):
        return requests.get(urljoin(self.base_url, url),
                            params=params,
                            headers={"X-Token": self.x_token})

    def post(self, url, params=None, files=None):
        return requests.post(urljoin(self.base_url, url),
                             params=params,
                             files=files,
                             headers={"X-Token": self.x_token})