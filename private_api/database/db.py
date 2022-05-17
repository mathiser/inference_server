import logging
import os
from typing import List, BinaryIO, Optional

from database import DBInterface, SQLiteImpl, Model, Task, Base
LOG_FORMAT = '%(levelname)s:%(asctime)s:%(message)s'
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)


class DBImpl(DBInterface):
    def __init__(self, declarative_base, base_dir="./mounts"):
        self.declarative_base = declarative_base
        # data volume mount point
        self.base_dir = base_dir
        self.sqlite_db = SQLiteImpl(declarative_base=declarative_base, base_dir=os.path.join(self.base_dir, "sqlite"))

    def add_task(self,
                 zip_file: BinaryIO,
                 human_readable_id: str,
                 uid: str) -> Task:
        return self.sqlite_db.add_task(zip_file=zip_file,
                                       human_readable_id=human_readable_id,
                                       uid=uid)

    def get_task_by_id(self, id: int) -> Task:
        return self.sqlite_db.get_task_by_id(id)

    def get_task_by_uid(self, uid: str) -> Task:
        return self.sqlite_db.get_task_by_uid(uid=uid)

    def get_tasks(self) -> List[Task]:
        return self.sqlite_db.get_tasks()

    def add_model(self,
                  container_tag: str,
                  human_readable_id: str,
                  input_mountpoint: str,
                  output_mountpoint: str,
                  zip_file: BinaryIO,
                  model_mountpoint: Optional[str] = None,
                  description: Optional[str] = None,
                  model_available: Optional[bool] = True,
                  use_gpu: Optional[bool] = True,
                  ) -> Model:
        return self.sqlite_db.add_model(container_tag=container_tag,
                                        human_readable_id=human_readable_id,
                                        input_mountpoint=input_mountpoint,
                                        output_mountpoint=output_mountpoint,
                                        zip_file=zip_file,
                                        model_mountpoint=model_mountpoint,
                                        description=description,
                                        model_available=model_available,
                                        use_gpu=use_gpu)

    def get_model_by_id(self, id: int) -> Model:
        return self.sqlite_db.get_model_by_id(id=id)

    def get_models(self) -> List[Model]:
        return self.sqlite_db.get_models()

    def post_output_by_uid(self, uid: str, zip_file: BinaryIO) -> Task:
        return self.sqlite_db.post_output_by_uid(uid=uid,
                                                 zip_file=zip_file)


DB = DBImpl(declarative_base=Base)