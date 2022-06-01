from fastapi.testclient import TestClient

from database_client.db_client_interface import DBClientInterface


class MockDBClient(DBClientInterface):
    def __init__(self, app):
        self.client = TestClient(app=app)

    def get(self, url, stream=False):
        return self.client.get(url=url)

    def post(self, url, params, files):
        return self.client.post(url=url, params=params, files=files)