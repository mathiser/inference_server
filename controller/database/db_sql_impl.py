import logging
import os
import secrets
import shutil
import traceback
from datetime import datetime
from io import BytesIO
from typing import List, Union, Optional

import sqlalchemy
from sqlalchemy.orm import sessionmaker, scoped_session

from database.db_interface import DBInterface
from database.db_models import Model, Task, Base
from .db_exceptions import TaskNotFoundException, ModelNotFoundException, \
    TaskTarPathExistsException, TarFileMissingException, ContradictingTarFileException


class DBSQLiteImpl(DBInterface):
    def __init__(self, base_dir, declarative_base=Base, log_level=10):
        LOG_FORMAT = '%(levelname)s:%(asctime)s:%(message)s'
        logging.basicConfig(level=log_level, format=LOG_FORMAT)
        self.logger = logging.getLogger(__name__)
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

        self.session_maker = sessionmaker(bind=self.engine, expire_on_commit=False)
        self.Session = scoped_session(self.session_maker)


    def purge(self):
        shutil.rmtree(self.base_dir)

    def post_task(self,
                  tar_file: BytesIO,
                  human_readable_id: str,
                  uid: Union[str, None] = None) -> Task:
        if not uid:
            uid = secrets.token_urlsafe()

        # Find the relevant model
        model = self.get_model(human_readable_id=human_readable_id)
        if model is None:
            raise ModelNotFoundException

        with self.Session() as session:
            # Define task
            try:
                task = Task(uid=uid,
                            model_id=model.id,
                            input_tar=os.path.abspath(os.path.join(self.input_base_folder, uid, "input.tar.gz")),
                            output_tar=os.path.abspath(os.path.join(self.output_base_folder, uid, "output.tar.gz")),
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
                os.makedirs(os.path.dirname(task.input_tar))
                os.makedirs(os.path.dirname(task.output_tar))
            except FileExistsError as e:
                raise TaskTarPathExistsException

            # Extract uploaded tarfile to input_folder
            with open(task.input_tar, 'wb') as out_file:
                out_file.write(tar_file.read())

            return task

    def get_task(self,
                 task_id: Union[int, None] = None,
                 task_uid: Union[str, None] = None) -> Union[Task, None]:
        with self.Session() as session:
            if task_id:
                return session.query(Task).filter_by(id=task_id, is_deleted=False).first()
            if task_uid:
                return session.query(Task).filter_by(uid=task_uid, is_deleted=False).first()

    def set_task_status(self, task_id: int, status: int) -> Task:
        with self.Session() as session:
            t = session.query(Task).filter_by(id=task_id).first()
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

    def get_tasks(self) -> List:
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
                    in_dir = os.path.dirname(t.input_tar)
                    if os.path.exists(in_dir):
                        shutil.rmtree(in_dir)

                    out_dir = os.path.dirname(t.output_tar)
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
                   tar_file: Optional[Union[BytesIO, None]] = None,
                   model_available: Union[bool, None] = None,
                   use_gpu: Union[bool, None] = None,
                   dump_logs: Union[bool, None] = None,
                   pull_on_every_run: Union[bool, None] = None) -> Model:
        
        model = Model(
            description=description,
            human_readable_id=human_readable_id,
            container_tag=container_tag,
            model_available=model_available,
            use_gpu=use_gpu,
            pull_on_every_run=pull_on_every_run,
            dump_logs=dump_logs
        )
        if model.model_available and not tar_file:
            raise TarFileMissingException

        if not model.model_available and tar_file:
            raise ContradictingTarFileException

        with self.Session() as session:
            session.add(model)
            session.commit()

            if model.model_available and tar_file:
                model.model_tar = os.path.join(self.model_base_folder, str(model.id), "model.tar.gz")
                os.makedirs(os.path.dirname(model.model_tar))
                # write model_tar to model_tar
                with open(model.model_tar, 'wb') as f:
                    f.write(tar_file.read())

            session.commit()
            session.refresh(model)
        
        return model

    def get_model(self,
                  model_id: Union[int, None] = None,
                  human_readable_id: Union[str, None] = None) -> Model:

        with self.Session() as session:
            # Prioritize model_id over human_readable_id
            if model_id:
                model = session.query(Model).filter_by(id=model_id).first()
            elif human_readable_id:
                model = session.query(Model).filter_by(human_readable_id=human_readable_id).first()

            # Return if found model or raise
            if model:
                return model
            else:
                raise ModelNotFoundException

    def get_models(self) -> List:
        with self.Session() as session:
            return list(session.query(Model))

    def post_output_tar(self, task_id: int, tar_file: BytesIO) -> Task:
        with self.Session() as session:
            # Get the task
            task = session.query(Task).filter_by(id=task_id).first()
            if not task:
                raise TaskNotFoundException

            try:
                # Write tar_file to task.output_tar
                with open(task.output_tar, 'wb') as out_file:
                    out_file.write(tar_file.read())
            except Exception as e:
                logging.error(e)
                raise e

            # Set task as finished and finished_datetime
            # Save changes
            session.commit()
            session.refresh(task)

        self.set_task_status(task.id, 1)
        return task
