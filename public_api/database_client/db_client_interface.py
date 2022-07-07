from abc import abstractmethod


class DBClientInterface:

    @abstractmethod
    def get(self, url, stream=False):
        pass

    @abstractmethod
    def post(self, url, params, files):
        pass

    @abstractmethod
    def delete(self, url):
        pass