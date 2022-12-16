from urllib.parse import urljoin

import requests

from interfaces.db_client_interface import DBClientInterface


class DBClientRequestsImpl(DBClientInterface):
    def __init__(self, base_url):
        self.base_url = base_url

    def get(self, url, stream=False):
        return requests.get(urljoin(self.base_url, url))

    def post(self, url, params, files=None):
        if files:
            return requests.post(urljoin(self.base_url, url), params=params, files=files)
        else:
            return requests.post(urljoin(self.base_url, url), params=params)

    def delete(self, url):
        return requests.delete(urljoin(self.base_url, url))
