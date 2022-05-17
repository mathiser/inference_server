import logging
import os
import secrets
import shutil
import uuid
from datetime import datetime
from typing import List, BinaryIO, Optional

import sqlalchemy
from sqlalchemy.orm import sessionmaker

from .db_interface import DBInterface
from .models import Model, Task

LOG_FORMAT = '%(levelname)s:%(asctime)s:%(message)s'
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)


class SQLiteImpl(DBInterface):
    def __init__(self, declarative_base, base_dir="./"):
        self.declarative_base = declarative_base

        # data volume mount point
        self.base_dir = base_dir

        # Folder for databse
        self.db_base_folder = os.path.join(self.base_dir, "")

        ## Folders for input and output
        self.input_base_folder = os.path.join(self.base_dir, "input")
        self.output_base_folder = os.path.join(self.base_dir, "output")

        # model volume mount point
        self.model_base_folder = os.path.join(self.base_dir, "models")

        # Create all folders
        for p in [self.base_dir, self.db_base_folder, self.input_base_folder, self.output_base_folder,
                  self.model_base_folder]:
            os.makedirs(p, exist_ok=True)

        self.database_path = f'{self.db_base_folder}/database.db'
        self.database_url = f'sqlite:///{self.database_path}'

        self.engine = sqlalchemy.create_engine(self.database_url, future=True)

        # Check if database exists - if not, create scheme
        if not os.path.exists(self.database_path):
            self.declarative_base.metadata.create_all(self.engine)

        self.Session = sessionmaker(bind=self.engine)

    def purge(self):
        shutil.rmtree(self.base_dir)

    def add_task(self,
                 zip_file: BinaryIO,
                 model_human_readable_id: str,
                 uid: str = None):

        if not uid:
            uid = secrets.token_urlsafe(32)

        with self.Session() as s:
            # Define task
            t = Task(uid=uid,
                     model_human_readable_id=model_human_readable_id,
                     input_zip=os.path.abspath(os.path.join(self.input_base_folder, uid, "input.zip")),
                     input_volume_uuid=str(uuid.uuid4()),
                     output_zip=os.path.abspath(os.path.join(self.output_base_folder, uid, "output.zip")),
                     output_volume_uuid=str(uuid.uuid4())
                     )
            # Commit task and refresh
            s.add(t)
            s.commit()
            s.refresh(t)

            # Make input and output dirs
            os.makedirs(os.path.dirname(t.input_zip))
            os.makedirs(os.path.dirname(t.output_zip))

            # Extract uploaded zipfile to input_folder
            with open(t.input_zip, 'wb') as out_file:
                out_file.write(zip_file.read())

            return t

    def get_task_by_id(self, id: int):
        with self.Session() as s:
            t = s.query(Task).filter_by(id=id).first()
            if t:
                return t
            else:
                raise Exception("Task not found")

    def get_task_by_uid(self, uid: str) -> Task:
        with self.Session() as s:
            t = s.query(Task).filter_by(uid=uid).first()
            if t:
                return t
            else:
                raise Exception("Task not found")

    def get_tasks(self) -> List[Task]:
        with self.Session() as s:
            tasks = s.query(Task)
            return list(tasks)

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
                  ):

        uid = str(uuid.uuid4())
        model_zip = None
        if model_available:
            model_zip = os.path.join(self.model_base_folder, uid, "model.zip")

        model = Model(
            uid=uid,
            description=description,
            human_readable_id=human_readable_id,
            container_tag=container_tag,
            model_zip=model_zip,
            model_volume_uuid=str(uuid.uuid4()),
            input_mountpoint=input_mountpoint,
            output_mountpoint=output_mountpoint,
            model_mountpoint=model_mountpoint,
            model_available=model_available,
            use_gpu=use_gpu
        )

        ## Add model to DB
        with self.Session() as s:
            s.add(model)
            s.commit()
            s.refresh(model)

        if model.model_available:
            os.makedirs(os.path.dirname(model.model_zip))
            # write model_zip to model_zip
            with open(model.model_zip, 'wb') as f:
                f.write(zip_file.read())

        return model

    def get_model_by_id(self, id: int) -> Model:
        with self.Session() as s:
            model = s.query(Model).filter_by(id=id).first()
            if model:
                return model
            else:
                raise Exception("Model not found")

    def get_model_by_human_readable_id(self, human_readable_id: str) -> Model:
        with self.Session() as s:
            model = s.query(Model).filter_by(human_readable_id=human_readable_id).first()
            if model:
                return model
            else:
                raise Exception("Model not found")

    def get_models(self) -> List[Model]:
        with self.Session() as s:
            return list(s.query(Model))

    def post_output_by_uid(self, uid: str, zip_file: BinaryIO) -> Task:
        with self.Session() as s:
            # Get the task
            t = s.query(Task).filter_by(uid=uid).first()

            # Write zip_file to task.output_zip
            with open(t.output_zip, 'wb') as out_file:
                out_file.write(zip_file.read())

            # Set task as finished and finished_datetime
            t.is_finished = True
            t.datetime_finished = datetime.utcnow()

            # Save changes
            s.commit()
            s.refresh(t)
            return t