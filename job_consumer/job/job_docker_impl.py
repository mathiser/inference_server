import logging
import os
import shutil
import tempfile
from typing import Dict
from urllib.parse import urljoin

import docker
from docker import types
from docker.errors import NotFound, ContainerError

from database.database_interface import DBInterface
from database.models import Task, Model
import requests
from job.job_exceptions import ModelNotSetException, TaskNotSetException
from job.job_interface import JobInterface
from docker_helper import volume_functions

from utils.file_handling import zip_folder_to_tmpfile


class JobDockerImpl(JobInterface):
    def __init__(self, db: DBInterface):
        self.db = db
        self.task = None
        self.model = None
        self.output_dir = None
        self.cli = docker.from_env()

    def __del__(self):
        if self.task:
            if volume_functions.volume_exists(self.task.input_volume_uuid):
                volume_functions.delete_volume(self.task.input_volume_uuid)

            if self.output_dir:
                shutil.rmtree(self.output_dir)
            # if volume_functions.volume_exists(self.task.output_volume_uuid):
            #     volume_functions.delete_volume(self.task.output_volume_uuid)

        self.cli.close()

    def set_task(self, task: Task):
        self.task = task
        return self.task

    def set_model(self, model: Model):
        self.model = model
        return self.model

    def execute(self):
        if not self.model:
            raise ModelNotSetException
        if not self.task:
            raise TaskNotSetException

        self.create_model_volume()
        self.create_input_volume()
        self.output_dir = tempfile.mkdtemp()

        try:
            volume_functions.pull_image(self.model.container_tag)
        except NotFound:
            pass


        job_container = self.cli.containers.run(image=self.model.container_tag,
                                                command=None,  # Already defaults to None, but for explicity
                                                remove=True,
                                                ports={80: []},  # Dummy port to make traefik shut up
                                                **self.generate_keywords())
        logging.info(job_container)

    def generate_keywords(self) -> Dict:
        ## Prepare docker keywords ###
        kw = {}

        ## Full access to ram
        kw["ipc_mode"] = "host"

        # Set input, output and model volumes // see https://docker-py.readthedocs.io/en/stable/containers.html
        kw["volumes"] = {}

        # Mount point of input to container
        kw["volumes"][self.task.input_volume_uuid] = {"bind": self.model.input_mountpoint,
                                                      "mode": "ro"}

        # Mount point of output to container
        kw["volumes"][self.output_dir] = {"bind": self.model.output_mountpoint,
                                                       "mode": "rw"}

        # Mount point of model volume to container if exists
        if self.model.model_available:
            kw["volumes"][self.model.model_volume_uuid] = {"bind": self.model.model_mountpoint,
                                                           "mode": "ro"}

        # Allow GPU usage if "use_gpu" is True
        if self.model.use_gpu:
            kw["device_requests"] = [
                docker.types.DeviceRequest(count=-1, capabilities=[['gpu']])]

        return kw

    def create_model_volume(self):
        if not self.model:
            raise ModelNotSetException

        if self.model.model_available:
            if not volume_functions.volume_exists(self.model.model_volume_uuid):
                with self.db.get_model_zip_by_id(self.model.id) as model_tmp_file:
                    volume_functions.create_volume_from_tmp_file(tmp_file=model_tmp_file,
                                                                 volume_uuid=self.model.model_volume_uuid)
            else:
                logging.info(f"Model {self.model.human_readable_id} has a docker volume already")
        else:
            logging.info(f"Model {self.model.human_readable_id}, does not have a model_zip")

    def create_input_volume(self):
        if not self.task:
            raise TaskNotSetException

        if not volume_functions.volume_exists(self.task.input_volume_uuid):
            with self.db.get_input_zip_by_id(self.task.id) as input_tmp_file:
                volume_functions.create_volume_from_tmp_file(tmp_file=input_tmp_file,
                                                             volume_uuid=self.task.input_volume_uuid)
        else:
            logging.info(f"Task {self.task.uid} has a docker volume already")

    def send_volume_output(self):
        url = os.environ.get('API_URL') + urljoin(os.environ.get('POST_OUTPUT_ZIP_BY_UID'), self.task.uid)
        tmp_zip = zip_folder_to_tmpfile(src=self.output_dir)
        res = requests.post(url, files={"zip_file": tmp_zip})
        print(res)
        res.raise_for_status()