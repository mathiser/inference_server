import tempfile
from abc import abstractmethod
from typing import Optional, BinaryIO

import requests


class DBInterface:
    @abstractmethod
    def post_task(self, model_human_readable_id: str,
                  zip_file: BinaryIO,
                  uid=None):
        pass

    @abstractmethod
    def get_output_zip_by_uid(self, uid: str) -> requests.Response:
        pass

    @abstractmethod
    def delete_task_by_uid(self, uid: str) -> requests.Response:
        pass

    @abstractmethod
    def post_model(self,
                   container_tag: str,
                   human_readable_id: str,
                   input_mountpoint: Optional[str] = None,
                   output_mountpoint: Optional[str] = None,
                   model_mountpoint: Optional[str] = None,
                   description: Optional[str] = None,
                   zip_file: Optional[BinaryIO] = None,
                   model_available: Optional[bool] = True,
                   use_gpu: Optional[bool] = True,
                   ):
        pass

    @abstractmethod
    def get_models(self):
        pass
