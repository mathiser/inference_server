import logging
import os
import secrets
from io import BytesIO
from typing import Union, Optional, Dict, List

from fastapi import FastAPI, File, UploadFile, HTTPException, Header
from fastapi.responses import FileResponse

from database.db_exceptions import TaskNotFoundException, ModelNotFoundException, InsertTaskException
from database.db_interface import DBInterface
from message_queue.mq_interface import MQInterface


class APIFastAPIImpl(FastAPI):
    def __init__(self, db: DBInterface, mq: MQInterface, x_token: str = secrets.token_urlsafe(32), log_level=10):
        super().__init__()
        LOG_FORMAT = '%(levelname)s:%(asctime)s:%(message)s'
        logging.basicConfig(level=log_level, format=LOG_FORMAT)
        self.logger = logging.getLogger(__name__)

        self.db = db
        self.mq = mq

        self.x_token = x_token

        self.threads = []

        self.task_endpoint = "/api/tasks/"
        self.input_endpoint = "/api/tasks/inputs/"
        self.output_endpoint = "/api/tasks/outputs/"
        self.model_endpoint = "/api/models/"
        self.model_tar_endpoint = "/api/models/tars/"

        @self.get("/")
        def hello_world():
            return {"message": "Hello world - Welcome to the public API"}

        @self.get(self.task_endpoint)
        def get_task(task_id: Union[int, None] = None, x_token: str = Header(default=None)) -> Union[List, Dict]:
            self.eval_token(x_token)

            if task_id:
                self.logger.info(f"Serving task with id {task_id}")
                return self.db.get_task(task_id=task_id).dict()
            else:
                self.logger.info(f"Serving all tasks")
                return list([t.dict() for t in self.db.get_tasks()])

        @self.put(self.task_endpoint)
        def set_task_status(task_id: int, status: int, x_token: str = Header(default=None)) -> Dict:
            self.logger.info(f"Updating task status to {status} of task_id {task_id}")
            self.eval_token(x_token)
            try:
                return self.db.set_task_status(task_id=task_id, status=status).dict()
            except TaskNotFoundException as e:
                raise HTTPException(status_code=554,
                                    detail=e.msg())

        @self.delete(self.task_endpoint)
        def delete_task(uid: str) -> Dict:
            self.eval_token(x_token)
            try:
                t = self.db.delete_task(uid=uid)
                return t.dict()
            except TaskNotFoundException as e:
                raise HTTPException(status_code=554,
                                    detail=e.msg())

        @self.post(self.task_endpoint)
        def post_task(human_readable_id: str,
                      tar_file: UploadFile = File(...)) -> Dict:
            self.logger.info(f"Receiving task on human_readable_id: {human_readable_id}")
            try:
                task = self.db.post_task(tar_file=BytesIO(tar_file.file.read()),
                                         human_readable_id=human_readable_id)
                self.mq.publish_unfinished_task(task)

            except InsertTaskException as e:
                raise HTTPException(status_code=554,
                                    detail=e.msg())

            return task.dict()

        @self.get(self.input_endpoint)
        def get_input_tar(task_id: int, x_token: str = Header(default=None)) -> FileResponse:
            self.eval_token(x_token)
            self.logger.info(f"Serving input_tar for task_id {task_id}")
            try:
                task = self.db.get_task(task_id=task_id)
            except TaskNotFoundException as e:
                raise HTTPException(status_code=554,
                                    detail=e.msg())

            if os.path.exists(task.input_tar):
                return FileResponse(task.input_tar)
            else:
                raise HTTPException(status_code=554, detail="Input tar not found - try posting task again")

        @self.post(self.output_endpoint)
        def post_output_tar(task_id: int,
                            tar_file: UploadFile = File(...),
                            x_token: str = Header(default=None)) -> Dict:
            self.eval_token(x_token)
            self.logger.info(f"Serving output_tar for task_id {task_id}")

            try:
                task = self.db.post_output_tar(task_id=task_id, tar_file=BytesIO(tar_file.file.read()))
                self.db.set_task_status(task_id=task_id, status=1)
            except TaskNotFoundException as e:
                raise HTTPException(status_code=554,
                                    detail=e.msg())
            except Exception as e:
                self.logger.error(str(e))
                raise e

            self.logger.info(task)
            self.mq.publish_finished_task(task)
            return task.dict()

        @self.post(self.model_endpoint)
        def post_model(container_tag: str,
                       human_readable_id: str,
                       description: Union[str, None] = None,
                       tar_file: Optional[Union[UploadFile, None]] = None,
                       model_available: Union[bool, None] = None,
                       use_gpu: Union[bool, None] = None,
                       dump_logs: Union[bool, None] = None,
                       pull_on_every_run: Union[bool, None] = None,
                       x_token: str = Header(default=None),
                       ) -> Dict:
            self.eval_token(x_token)

            if tar_file:
                tar_file = tar_file.file

            model = self.db.post_model(
                container_tag=container_tag,
                human_readable_id=human_readable_id,
                tar_file=tar_file,
                description=description,
                model_available=model_available,
                use_gpu=use_gpu,
                pull_on_every_run=pull_on_every_run,
                dump_logs=dump_logs
            )
            self.logger.info(f"Receiving model {model.dict()}")
            return model.dict()

        @self.get(self.model_endpoint)
        def get_model(model_id: Union[int, None] = None,
                      human_readable_id: Union[str, None] = None,
                      x_token: str = Header(default=None)) -> Union[Dict, List]:
            self.eval_token(x_token)
            try:
                if model_id:
                    self.logger.info(f"Serving model with id {model_id}")
                    return self.db.get_model(model_id=model_id).dict()
                elif human_readable_id:
                    return self.db.get_model(human_readable_id=human_readable_id).dict()
                elif not model_id and not human_readable_id:
                    return list([m.dict() for m in self.db.get_models()])
            except Exception as e:
                raise HTTPException(status_code=400,
                                    detail=str(e))

        @self.get(self.model_tar_endpoint)
        def get_model_tar(model_id: int,
                          x_token: str = Header(default=None)) -> FileResponse:
            self.eval_token(x_token)
            try:
                model = self.db.get_model(model_id=model_id)
            except ModelNotFoundException as e:
                raise HTTPException(status_code=404,
                                    detail=e.msg())

            if model.model_available and os.path.exists(model.model_tar):
                return FileResponse(model.model_tar)
            else:
                raise HTTPException(status_code=404, detail="Model tar not found")

        @self.get(self.output_endpoint)
        def get_output_tar(uid: str) -> FileResponse:
            # tar the output for return
            try:
                task = self.db.get_task(task_uid=uid)
                self.logger.info(str(task.dict()))
            except TaskNotFoundException as e:
                raise HTTPException(status_code=554,
                                    detail=e.msg())

            # Not doing this with os.path.exists(task.output.tar) to avoid that some of the file is sent before all written
            if os.path.exists(task.output_tar) and task.status == 1:
                return FileResponse(task.output_tar)

            elif not os.path.exists(task.output_tar) and task.status == 1:
                raise HTTPException(status_code=553,
                                    detail="Job status is 'finished', but output tar does not exist")
            elif task.is_deleted == 1:
                raise HTTPException(status_code=552,
                                    detail="Job files are 'deleted'")
            elif task.status == 0:
                raise HTTPException(status_code=552,
                                    detail="Job status is 'failed'")
            elif task.status in [-1, 2]:
                raise HTTPException(status_code=551,
                                    detail="Job status is 'pending' or 'running'")
            else:
                self.logger.error(str(task))
                raise HTTPException(status_code=500,
                                    detail="Internal Server Error - should not be possible")

    def eval_token(self, x_token):
        if x_token != self.x_token:
            raise HTTPException(status_code=400, detail="Authentication error")