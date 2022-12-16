import logging
import os
from typing import Dict, Union
from urllib.parse import urljoin

import docker
from docker import types
from docker_helper import volume_functions
from interfaces.database_interface import DBInterface
from interfaces.db_models import Task, Model
from interfaces.job_interface import JobInterface
from job.job_exceptions import ModelNotSetException, TaskNotSetException


class JobDockerImpl(JobInterface):
    def __init__(self,
                 db: DBInterface,
                 api_url: str,
                 api_output_zips: str,
                 volume_sender_docker_tag: str,
                 network_name: str,
                 gpu_uuid: Union[str, None] = None
                 ):
        self.db = db
        self.task = None
        self.model = None
        self.cli = docker.from_env()

        self.api_url = api_url
        self.api_output_zips = api_output_zips
        self.volume_sender_docker_tag = volume_sender_docker_tag
        self.network_name = network_name
        self.gpu_uuid = gpu_uuid

        self.volume_sender = "volume_sender:temp"

        os.environ["LOG_LEVEL"] = "10"

    def __del__(self):
        if self.task:
            if volume_functions.volume_exists(self.task.input_volume_id):
                volume_functions.delete_volume(self.task.input_volume_id)

            if volume_functions.volume_exists(self.task.output_volume_id):
                volume_functions.delete_volume(self.task.output_volume_id)

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
        volume_functions.create_empty_volume(self.task.output_volume_id)

        try:
            volume_functions.pull_image(self.model.container_tag)
        except Exception as e:
            logging.error(e)

        job_container = self.cli.containers.run(image=self.model.container_tag,
                                                command=None,  # Already defaults to None, but for explicity
                                                remove=True,
                                                ports={80: []},  # Dummy port to make traefik shut up
                                                **self.generate_keywords())
        logging.info(job_container)
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
        if self.model.model_available:
            kw["volumes"][self.model.model_volume_id] = {"bind": "/model",
                                                         "mode": "ro"}

        # Allow GPU usage if "use_gpu" is True
        if self.model.use_gpu:
            if self.gpu_uuid:
                kw["device_requests"] = [
                    docker.types.DeviceRequest(device_ids=[self.gpu_uuid], capabilities=[['gpu']])]
            else:
                kw["device_requests"] = [
                    docker.types.DeviceRequest(count=-1, capabilities=[['gpu']])]

        logging.debug(str(kw))
        return kw

    def create_model_volume(self):
        if not self.model:
            raise ModelNotSetException

        if self.model.model_available:
            if not volume_functions.volume_exists(self.model.model_volume_id):
                with self.db.get_model_zip(self.model.uid) as model_tmp_file:
                    volume_functions.create_volume_from_tmp_file(tmp_file=model_tmp_file,
                                                                 volume_id=self.model.model_volume_id)
            else:
                logging.info(f"Model {self.model.human_readable_id} has a docker volume already")
        else:
            logging.info(f"Model {self.model.human_readable_id}, does not have a model_zip, which is fine!")

    def create_input_volume(self):
        if not self.task:
            raise TaskNotSetException

        if not volume_functions.volume_exists(self.task.input_volume_id):
            with self.db.get_input_zip(self.task.uid) as input_tmp_file:
                volume_functions.create_volume_from_tmp_file(tmp_file=input_tmp_file,
                                                             volume_id=self.task.input_volume_id)
        else:
            logging.info(f"Task {self.task.uid} has a docker volume already")

    def send_volume_output(self):
        url = self.api_url + urljoin(self.api_output_zips, self.task.uid)
        logging.info("URL to post on: {}".format(url))
        self.build_volume_sender(self.volume_sender)
        tmp_container = self.cli.containers.run(self.volume_sender,
                                                volumes={self.task.output_volume_id: {"bind": '/data', 'mode': 'ro'}},
                                                environment={
                                                    "URL": url,
                                                    "VOLUME_MOUNTPOINT": "/data"
                                                },
                                                remove=True,
                                                ports={80: []},  ## Dummyport to make traefik shut up
                                                network=self.network_name)
        logging.info(tmp_container)

    def build_volume_sender(self, tag):
        p = os.path.abspath("volume_sender")
        if not volume_functions.image_exists(tag):
            volume_functions.build_image(path=p, tag=tag)
        else:
            logging.info(f"{tag} image exists")
