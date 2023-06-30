from abc import abstractmethod


class DBClientInterface:
    @abstractmethod
    def __init__(self, base_url: str, x_token: str):
        pass

    @abstractmethod
    def get(self, url, params=None):
        pass

    @abstractmethod
    def post(self, url, params=None, files=None):
        pass

    @abstractmethod
    def put(self, url, params=None):
        pass
