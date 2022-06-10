import os
import tempfile
from typing import Any, Optional
from urllib.parse import urljoin

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
from testing.mock_components.models import Task, Model


class MockPrivateFastAPI(FastAPI):
    def __init__(self, db, **extra: Any):
        super().__init__(**extra)
        self.db = db

        @self.get("/")
        def hello_world():
            return {"message": "Hello world - Welcome to the public database API"}

        @self.post(os.environ['POST_TASK'])
        def post_task(model_human_readable_id: str,
                      zip_file: UploadFile = File(...),
                      uid=None) -> Task:

            t = self.db.post_task(zip_file=zip_file.file,
                                   model_human_readable_id=model_human_readable_id,
                                   uid=uid)
            return t


        @self.get(urljoin(os.environ['GET_OUTPUT_ZIP_BY_UID'], "{uid}"))
        def get_output_zip_by_uid(uid: str):
            # Zip the output for return
            output_tmp_file = self.db.get_output_zip_by_uid(uid=uid)
            if output_tmp_file is None:
                raise HTTPException(status_code=404,
                                    detail="Task not in DB yet. If you very recently uploaded it - or uploaded a very large file - try again in a moment")

            def iterfile():
                with tempfile.TemporaryFile() as tmp_file:
                    for chunk in output_tmp_file.iter_content(1000000):
                        tmp_file.write(chunk)
                    tmp_file.seek(0)

                    yield from tmp_file
            return StreamingResponse(iterfile())


        @self.post(os.environ['POST_MODEL'])
        def post_model(container_tag: str,
                       human_readable_id: str,
                       input_mountpoint: Optional[str] = None,
                       output_mountpoint: Optional[str] = None,
                       model_mountpoint: Optional[str] = None,
                       description: Optional[str] = None,
                       zip_file: Optional[UploadFile] = File(None),
                       model_available: Optional[bool] = True,
                       use_gpu: Optional[bool] = True,
                       ) -> Model:

            return self.db.post_model(
                container_tag=container_tag,
                human_readable_id=human_readable_id,
                input_mountpoint=input_mountpoint,
                output_mountpoint=output_mountpoint,
                zip_file=zip_file.file,
                model_mountpoint=model_mountpoint,
                description=description,
                model_available=model_available,
                use_gpu=use_gpu
            )



        @self.get(os.environ['GET_MODELS'])
        def get_models():
            return self.db.get_models()

