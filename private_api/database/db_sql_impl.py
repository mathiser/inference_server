import logging
import os
import secrets
import shutil
import uuid
from datetime import datetime
from typing import List, BinaryIO, Union, Optional

import sqlalchemy
from sqlalchemy.orm import sessionmaker

from .db_exceptions import TaskNotFoundException, ModelNotFoundException, \
    TaskZipPathExistsException, InsertTaskException, ZipFileMissingException, ContradictingZipFileException, \
    ModelInsertionException, TaskInitializationException, ModelMountPointMissingException
from .db_interface import DBInterface
from .models import Model, Task, Base

LOG_FORMAT = '%(levelname)s:%(asctime)s:%(message)s'
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)


class DBSQLiteImpl(DBInterface):
    def __init__(self, base_dir, declarative_base=Base):
        self.declarative_base = declarative_base

        # data volume mount point
        self.base_dir = base_dir

        # Folder for databse
        self.db_base_folder = os.path.join(self.base_dir, "database")

        ## Folders for input and output
        self.input_base_folder = os.path.join(self.base_dir, "inputs")
        self.output_base_folder = os.path.join(self.base_dir, "outputs")

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

    def post_task(self,
                  zip_file: BinaryIO,
                  model_human_readable_id: str,
                  uid: str = None):

        if not uid:
            uid = secrets.token_urlsafe(32)

        with self.Session() as session:
            # Define task
            try:
                task = Task(uid=uid,
                            model_human_readable_id=model_human_readable_id,
                            input_zip=os.path.abspath(os.path.join(self.input_base_folder, uid, "input.zip")),
                            input_volume_uuid=str(uuid.uuid4()),
                            output_zip=os.path.abspath(os.path.join(self.output_base_folder, uid, "output.zip")),
                            output_volume_uuid=str(uuid.uuid4())
                            )

            except Exception as e:
                logging.error(e)
                raise TaskInitializationException

            # Commit task and refresh
            try:
                session.add(task)
                session.commit()
                session.refresh(task)

            except Exception as e:
                print(e)
                raise InsertTaskException

            # Make input and output dirs
            try:
                os.makedirs(os.path.dirname(task.input_zip))
                os.makedirs(os.path.dirname(task.output_zip))
            except FileExistsError:
                raise TaskZipPathExistsException

            # Extract uploaded zipfile to input_folder
            with open(task.input_zip, 'wb') as out_file:
                out_file.write(zip_file.read())

            return task

    def get_task_by_id(self, id: int):
        with self.Session() as session:
            task = session.query(Task).filter_by(id=id).first()
            if task:
                return task
            else:
                raise TaskNotFoundException

    def get_task_by_uid(self, uid: str) -> Task:
        with self.Session() as session:
            t = session.query(Task).filter_by(uid=uid).first()
            if t:
                return t
            else:
                raise TaskNotFoundException

    def get_tasks(self) -> List[Task]:
        with self.Session() as session:
            tasks = session.query(Task)
            return list(tasks)

    def post_model(self,
                   container_tag: str,
                   human_readable_id: str,
                   input_mountpoint: Union[str, None] = None,
                   output_mountpoint: Union[str, None] = None,
                   model_mountpoint: Union[str, None] = None,
                   description: Union[str, None] = None,
                   zip_file: Optional[Union[BinaryIO, None]] = None,
                   model_available: Union[bool, None] = None,
                   use_gpu: Union[bool, None] = None
                   ):

        model = Model(
            uid=str(uuid.uuid4()),
            description=description,
            human_readable_id=human_readable_id,
            container_tag=container_tag,
            input_mountpoint=input_mountpoint,
            output_mountpoint=output_mountpoint,
            model_mountpoint=model_mountpoint,
            model_available=model_available,
            use_gpu=use_gpu
        )

        if model.model_available and zip_file:
            if not model_mountpoint:
                raise ModelMountPointMissingException

            model.model_volume_uuid = str(uuid.uuid4())
            model.model_zip = os.path.join(self.model_base_folder, model.uid, "model.zip")
            os.makedirs(os.path.dirname(model.model_zip))
            # write model_zip to model_zip
            with open(model.model_zip, 'wb') as f:
                f.write(zip_file.read())

        elif model.model_available and not zip_file:
            raise ZipFileMissingException

        elif not model.model_available and zip_file:
            raise ContradictingZipFileException

        try:
            ## Add model to DB
            with self.Session() as session:
                session.add(model)
                session.commit()
                session.refresh(model)
        except Exception as e:
            logging.error(e)
            raise ModelInsertionException

        return model

    def get_model_by_id(self, id: int) -> Model:
        with self.Session() as session:
            model = session.query(Model).filter_by(id=id).first()
            if model:
                return model
            else:
                raise ModelNotFoundException

    def get_model_by_human_readable_id(self, human_readable_id: str) -> Model:
        with self.Session() as session:
            model = session.query(Model).filter_by(human_readable_id=human_readable_id).first()
            if model:
                return model
            else:
                raise ModelNotFoundException

    def get_models(self) -> List[Model]:
        with self.Session() as session:
            return list(session.query(Model))

    def post_output_zip_by_uid(self, uid: str, zip_file: BinaryIO) -> Task:
        with self.Session() as session:
            # Get the task
            task = session.query(Task).filter_by(uid=uid).first()
            if not task:
                raise TaskNotFoundException

            try:
                # Write zip_file to task.output_zip
                with open(task.output_zip, 'wb') as out_file:
                    out_file.write(zip_file.read())
            except Exception as e:
                logging.error(e)
                raise e

            # Set task as finished and finished_datetime
            task.is_finished = True
            task.datetime_finished = datetime.utcnow()

            # Save changes
            session.commit()
            session.refresh(task)
            return task
