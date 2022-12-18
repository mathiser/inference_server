import logging
import os
import secrets
import shutil
import traceback
from datetime import datetime
from typing import List, BinaryIO, Union, Optional

import sqlalchemy
from sqlalchemy.orm import sessionmaker, scoped_session

from interfaces.db_interface import DBInterface
from interfaces.db_models import Model, Task, Base
from .db_exceptions import TaskNotFoundException, ModelNotFoundException, \
    TaskZipPathExistsException, ZipFileMissingException, ContradictingZipFileException

LOG_FORMAT = '%(levelname)s:%(asctime)s:%(message)s'
logging.basicConfig(level=int(os.environ.get("LOG_LEVEL")), format=LOG_FORMAT)

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

        self.session_maker = sessionmaker(bind=self.engine)
        self.Session = scoped_session(self.session_maker)

    def purge(self):
        shutil.rmtree(self.base_dir)

    def post_task(self,
                  zip_file: BinaryIO,
                  model_human_readable_id: str,
                  uid: str = None):

        if not uid:
            uid = secrets.token_urlsafe()

        with self.Session() as session:
            # Define task
            try:
                task = Task(uid=uid,
                            model_human_readable_id=model_human_readable_id,
                            input_zip=os.path.abspath(os.path.join(self.input_base_folder, uid, "input.zip")),
                            output_zip=os.path.abspath(os.path.join(self.output_base_folder, uid, "output.zip")),
                            )

                # Commit task and refresh
                session.add(task)
                session.commit()
                session.refresh(task)

            except Exception as e:
                traceback.print_exc()
                raise e

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


    def get_task(self, uid: str) -> Task:
        with self.Session() as session:
            t = session.query(Task).filter_by(uid=uid, is_deleted=False).first()
            if t:
                return t
            else:
                raise TaskNotFoundException

    def set_task_status(self, uid: str, status: int) -> Task:
        with self.Session() as session:
            t = session.query(Task).filter_by(uid=uid).first()
            if t:
                t.status = status
                if status in [0, 1]:
                    t.datetime_finished = datetime.now()
                elif status == 2:
                    t.datetime_dispatched = datetime.now()
                session.commit()
                session.refresh(t)
                return t
            else:
                raise TaskNotFoundException

    def get_tasks(self) -> List[Task]:
        with self.Session() as session:
            tasks = session.query(Task)
            return list(tasks)

    def delete_task(self, uid: str) -> Task:
        with self.Session() as session:
            t = session.query(Task).filter_by(uid=uid, is_deleted=False).first()
            if t:
                # If task is running -> cannot delete
                if t.status == 2:
                    raise Exception("Cannot delete a running task")
                if t.status in [-1, 0, 1]:
                    in_dir = os.path.dirname(t.input_zip)
                    if os.path.exists(in_dir):
                        shutil.rmtree(in_dir)

                    out_dir = os.path.dirname(t.output_zip)
                    if os.path.exists(out_dir):
                        shutil.rmtree(out_dir)

                    t.is_deleted = True
                    if t.status == -1:
                        t.status = 0
                    session.commit()
                    session.refresh(t)
                    return t
            else:
                raise TaskNotFoundException

    def post_model(self,
                   container_tag: str,
                   human_readable_id: str,
                   description: Union[str, None] = None,
                   zip_file: Optional[Union[BinaryIO, None]] = None,
                   model_available: Union[bool, None] = None,
                   use_gpu: Union[bool, None] = None):

        model = Model(
            uid=secrets.token_hex(),
            description=description,
            human_readable_id=human_readable_id,
            container_tag=container_tag,
            model_available=model_available,
            use_gpu=use_gpu
        )
        if model.model_available and not zip_file:
            raise ZipFileMissingException

        if not model.model_available and zip_file:
            raise ContradictingZipFileException

        if model.model_available and zip_file:
            model.model_volume_id = model.uid
            model.model_zip = os.path.join(self.model_base_folder, model.uid, "model.zip")
            os.makedirs(os.path.dirname(model.model_zip))
            # write model_zip to model_zip
            with open(model.model_zip, 'wb') as f:
                f.write(zip_file.read())
        try:
            ## Add model to DB
            with self.Session() as session:
                session.add(model)
                session.commit()
                session.refresh(model)
        except Exception as e:
            raise e

        return model

    def get_model(self,
                  uid: Union[str, None] = None,
                  human_readable_id: Union[str, None] = None) -> Model:

        with self.Session() as session:
            # Prioritize uid over human_readable_id
            if uid:
                model = session.query(Model).filter_by(uid=uid).first()
            elif human_readable_id:
                model = session.query(Model).filter_by(human_readable_id=human_readable_id).first()

            # Return if found model or raise
            if model:
                return model
            else:
                raise ModelNotFoundException

    def get_models(self) -> List[Model]:
        with self.Session() as session:
            return list(session.query(Model))

    def post_output_zip(self, uid: str, zip_file: BinaryIO) -> Task:
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
            # Save changes
            session.commit()
            session.refresh(task)
        self.set_task_status(task.uid, 1)
        return task
