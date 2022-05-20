import logging
import os
import tarfile
import tempfile
import uuid
from typing import Dict, BinaryIO
from urllib.parse import urljoin

import docker
from docker import types

from job.job_interface import JobInterface
from database.models import Task, Model
from utils import file_handling

from database.database_interface import DBInterface


class JobDockerImpl(JobInterface):
    def __init__(self, db: DBInterface):
        self.db = db
        self.task = None
        self.model = None
        self.cli = docker.from_env()

    def __del__(self):
        if self.task:
            if self.volume_exists(self.task.input_volume_uuid):
                self.delete_volume(self.task.input_volume_uuid)

            if self.volume_exists(self.task.output_volume_uuid):
                self.delete_volume(self.task.output_volume_uuid)

        self.cli.close()

    def set_task(self, task: Task):
        self.task = task
        return self.task

    def set_model(self, model: Model):
        self.model = model
        return self.model

    def execute(self):
        if not self.model:
            raise Exception("Model must be set before execution")
        if not self.task:
            raise Exception("Task must be set before execution")

        self.create_model_volume()
        self.create_input_volume()
        self.create_empty_volume(self.task.output_volume_uuid)

        self.cli.images.pull(self.model.container_tag)
        self.job_container = self.cli.containers.run(image=self.model.container_tag,
                                                command=None,  # Already defaults to None, but for explicity
                                                **self.generate_keywords()
                                                )
        logging.info(self.job_container)

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
        kw["volumes"][self.task.output_volume_uuid] = {"bind": self.model.output_mountpoint,
                                                       "mode": "rw"}

        # Mount point of model volume to container if exists
        if self.model.model_available:
            kw["volumes"][self.model.model_volume_uuid] = {"bind": self.model.model_mountpoint,
                                                           "mode": "ro"}

        # Allow GPU usage if "use_gpu" is True
        if self.model.use_gpu:
            kw["device_requests"] = [
                docker.types.DeviceRequest(count=-1, capabilities=[['gpu']])]

        kw["remove"] = True
        return kw

    def volume_exists(self, volume_uuid):
        return volume_uuid in [v.name for v in self.cli.volumes.list()]

    def create_model_volume(self):
        if not self.model:
            raise Exception("Model must be set before execution")

        if self.model.model_available:
            if not self.volume_exists(self.model.model_volume_uuid):
                with self.db.get_model_zip_by_id(self.model.id) as model_tmp_file:
                    self.create_volume_from_tmp_file(tmp_file=model_tmp_file, volume_uuid=self.model.model_volume_uuid)
            else:
                logging.info(f"Model {self.model.human_readable_id} has a docker volume already")
        else:
            logging.info(f"Model {self.model.human_readable_id}, does not have a model_zip")

    def create_input_volume(self):
        if not self.task:
            raise Exception("Task must be set before execution")

        if not self.volume_exists(self.task.input_volume_uuid):
            with self.db.get_input_zip_by_id(self.task.id) as input_tmp_file:
                self.create_volume_from_tmp_file(tmp_file=input_tmp_file, volume_uuid=self.task.input_volume_uuid)
        else:
            logging.info(f"Task {self.task.uid} has a docker volume already")

    def delete_volume(self, volume_uuid):
        if self.volume_exists(volume_uuid=volume_uuid):
            return self.cli.volumes.get(volume_uuid).remove()

    def create_volume_from_tmp_file(self, tmp_file: BinaryIO, volume_uuid=None):
        if not volume_uuid:
            volume_uuid = str(uuid.uuid4())

        # Pull_model_zip_and_extract_to_tmp
        # Set a tmp path and create
        with tempfile.TemporaryDirectory() as tmp_vol_folder:
            vol_dir = os.path.join(tmp_vol_folder, "vol")

            # Stream content to temp file and unzip to tmp_vol_folder
            # Returns the model folder path
            file_handling.unzip_tmp_file_to_location(tmp_file, vol_dir)

            # Create docker volume named with uid.
            self.cli.volumes.create(name=volume_uuid)

            # Create a helper container and mount
            self.cli.images.pull(os.environ.get("BUSYBOX_DOCKER_TAG"))
            tmp_container = self.cli.containers.create(image=os.environ.get("BUSYBOX_DOCKER_TAG"),
                                                       command=None,
                                                       volumes={volume_uuid: {"bind": "/data", "mode": "rw"}},
                                                       )
            # Tar and untar the tmp_vol_folder to /data
            with tempfile.TemporaryDirectory() as tar_folder:
                tar_file = os.path.join(tar_folder, "tarfile")
                with tarfile.TarFile(tar_file, mode="w") as tar:
                    for file in os.listdir(vol_dir):
                        tar.add(os.path.join(vol_dir, file), arcname=file)

                with open(tar_file, "rb") as r:
                    tmp_container.put_archive("/data", r.read())

        # Remove the container - We have sucessfully made a volume with the model folder on.
        tmp_container.remove()

        return volume_uuid

    def create_empty_volume(self, volume_uuid=None) -> str:
        # Create docker volume named with uid.
        if not volume_uuid:
            volume_uuid = str(uuid.uuid4())
            self.cli.volumes.create(name=volume_uuid)
        return volume_uuid

    def send_volume_output(self):
        url = os.environ.get('API_URL') + urljoin(os.environ.get('POST_OUTPUT_ZIP_BY_UID'), self.task.uid)
        logging.info("URL to post on: {}".format(url))
        self.cli.images.pull(os.environ.get("VOLUME_SENDER_DOCKER_TAG"))
        tmp_container = self.cli.containers.run(os.environ.get("VOLUME_SENDER_DOCKER_TAG"),
                                           None,
                                           volumes={self.task.output_volume_uuid: {"bind": '/data', 'mode': 'ro'}},
                                           environment={
                                               "URL": url,
                                               "VOLUME_MOUNTPOINT": "/data"
                                           },
                                           remove=True,
                                           network=os.environ.get("NETWORK_NAME"))
        logging.info(tmp_container)
