import logging
from typing import Dict, Union

import docker
from docker import types

from database.db_models import Task
from docker_helper import volume_functions
from job.job_interface import JobInterface


class JobDockerImpl(JobInterface):
    def __init__(self,
                 task: Task,
                 gpu_uuid: Union[str, None] = None,
                 log_level=10,
                 ):
        LOG_FORMAT = '%(levelname)s:%(asctime)s:%(message)s'
        logging.basicConfig(level=log_level, format=LOG_FORMAT)
        self.logger = logging.getLogger(__name__)

        self.task = task

        self.cli = docker.from_env()

        self.gpu_uuid = gpu_uuid

    def __del__(self):
        self.cli.close()

    def execute(self):
        try:
            volume_functions.pull_image(self.task.model.container_tag)
        except Exception as e:
            self.logger.error(e)

        job_container = self.cli.containers.run(image=self.task.model.container_tag,
                                                command=None,  # Already defaults to None, but for explicity
                                                remove=True,
                                                ports={80: []},  # Dummy port to make traefik shut up
                                                **self.generate_keywords())
        self.logger.info(job_container)
        return job_container

    def generate_keywords(self) -> Dict:
        ## Prepare docker keywords ###
        kw = {}

        ## Full access to ram
        kw["ipc_mode"] = "host"

        # Set input, output and model volumes // see https://docker-py.readthedocs.io/en/stable/containers.html
        kw["volumes"] = {}

        # Mount point of input to container
        kw["volumes"][self.task.input_volume_id] = {"bind": "/input",
                                                    "mode": "ro"}

        # Mount point of output to container
        kw["volumes"][self.task.output_volume_id] = {"bind": "/output",
                                                     "mode": "rw"}

        # Mount point of model volume to container if exists
        if self.task.model.model_available:
            kw["volumes"][self.task.model.model_volume_id] = {"bind": "/model",
                                                              "mode": "ro"}

        # Allow GPU usage if "use_gpu" is True
        if self.task.model.use_gpu:
            self.logger.info(f"GPU UUID: {self.gpu_uuid}")
            if self.gpu_uuid == "-1":
                kw["device_requests"] = [
                    docker.types.DeviceRequest(count=-1, capabilities=[['gpu']])]
            else:
                kw["device_requests"] = [
                    docker.types.DeviceRequest(device_ids=[self.gpu_uuid], capabilities=[['gpu']])]

        self.logger.debug(str(kw))
        return kw
