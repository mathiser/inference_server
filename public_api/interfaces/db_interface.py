from abc import abstractmethod
from typing import Optional, BinaryIO


class DBInterface:
    @abstractmethod
    def post_task(self, model_human_readable_id: str,
                  zip_file: BinaryIO,
                  uid: str):
        pass

    @abstractmethod
    def get_output_zip(self, uid: str):
        pass

    @abstractmethod
    def delete_task(self, uid: str):
        pass

    @abstractmethod
    def post_model(self,
                   container_tag: str,
                   human_readable_id: str,
                   description: Optional[str] = None,
                   zip_file: Optional[BinaryIO] = None,
                   model_available: Optional[bool] = True,
                   use_gpu: Optional[bool] = True,
                   ):
        pass

    @abstractmethod
    def get_models(self):
        pass
