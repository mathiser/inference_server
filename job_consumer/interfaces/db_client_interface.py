from abc import abstractmethod


class DBClientInterface:

    @abstractmethod
    def get(self, url, stream=False):
        pass

    @abstractmethod
    def post(self, url, params=None, files=None):
        pass

    @abstractmethod
    def put(self, url, params=None):
        pass
