import logging

import docker

from .api_calls import get_model_by_id, get_model_zip_by_id
from .docker_volumes_methods import create_volume_from_response, volume_exists

LOG_FORMAT = ('%(levelname)s:%(asctime)s:%(message)s')
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)


class DockerJobHandler:
    def __init__(self, task_uid, model, input_volume_uuid, output_volume_uuid):
        if not volume_exists(input_volume_uuid) or not volume_exists(output_volume_uuid):
            raise Exception("Either input volume output volume must exist")

        self.input_volume_uuid = input_volume_uuid
        self.output_volume_uuid = output_volume_uuid
        self.model = model
        self.model_volume_uuid = self.model["model_volume"]
        self.task_uid = task_uid
        self.cli = docker.from_env()
        self.kw = {}

        # Set keywords for container
        self.set_keywords()

        if self.model["model_available"]:
            if not volume_exists(self.model_volume_uuid):
                create_volume_from_response(get_model_zip_by_id(self.model["id"]), volume_uuid=self.model_volume_uuid)

    def set_keywords(self):
        ## Prepare docker keywords ###
        self.kw = {}

        ## Full access to ram
        self.kw["ipc_mode"] = "host"

        # Set input, output and model volumes // see https://docker-py.readthedocs.io/en/stable/containers.html
        self.kw["volumes"] = {}

        # Mount point of input to container
        self.kw["volumes"][self.input_volume_uuid] = {"bind": self.model["input_mountpoint"],
                                                      "mode": "ro"}

        # Mount point of output to container
        self.kw["volumes"][self.output_volume_uuid] = {"bind": self.model["output_mountpoint"],
                                                       "mode": "rw"}

        # Mount point of model volume to container if exists
        if self.model["model_available"]:
            self.kw["volumes"][self.model_volume_uuid] = {"bind": self.model["model_mountpoint"],
                                                          "mode": "ro"}

        # Allow GPU usage if "use_gpu" is True
        if self.model["use_gpu"]:
            self.kw["device_requests"] = [
                docker.types.DeviceRequest(count=-1, capabilities=[['gpu']])]

        self.kw["remove"] = True

    def run(self):
        logging.info(f"{self.task_uid} Running job!")
        logging.info(f"{self.task_uid} Task: {self.task_uid}")
        logging.info(f"{self.task_uid} Model: {self.model}")
        logging.info(f"{self.task_uid} Keywords: {self.kw}")

        try:
            tmp_container = self.cli.containers.run(image=self.model["container_tag"],
                                    command=None,  # Already defaults to None, but for explicity
                                    **self.kw)
            logging.info(tmp_container)
        except Exception as e:
            logging.error(e)

    def get_input_volume_uuid(self):
        return self.input_volume_uuid

    def get_output_volume_uuid(self):
        return self.output_volume_uuid

    def close(self):
        self.cli.close()