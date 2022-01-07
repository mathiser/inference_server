import logging
import os

import docker

from api_calls import *
from file_handling import *

LOG_FORMAT = ('%(levelname)s:%(asctime)s:%(message)s')
logging.basicConfig(level=logging.DEBUG, format=LOG_FORMAT)

class DockerHandler:
    def __init__(self, input_folder, output_folder, model, task):
        self.input_folder = input_folder
        self.output_folder = output_folder
        self.model = model
        self.task = task
        self.cli = docker.from_env()
        self.kw = {}

        # Set keywords for container
        self.set_keywords()

        ## Check if model exists, else pull and create volume:
        if not self.volume_exists():
            logging.info("Model volume does not exit. Pulling from db and creating")
            self.create_volume()

    def volume_exists(self):
        return self.model["model_volume"] in [v.name for v in self.cli.volumes.list()]

    def create_volume(self):
        # Pull_model_zip_and_extract_to_tmp
        # Set a tmp path and create
        self.tmp_model_folder = os.path.join("/tmp", self.model["model_volume"])
        if not os.path.exists(self.tmp_model_folder):
            os.makedirs(self.tmp_model_folder)

        # Stream content to temp file and unzip to tmp_model_folder
        # Returns the model folder path
        unzip_response_to_location(get_model_zip_by_id(self.model["id"]), self.tmp_model_folder)

        # Create docker volume named self.model["model_volume"] --> This is the uid of the model.
        self.cli.volumes.create(name=self.model["model_volume"])

        # Create a helper container and mount
        tmp_container = self.cli.containers.create(image="busybox",
                                                   command="true",
                                                   volumes={self.model["model_volume"]: {"bind": "/data", "mode": "rw"}}
                                                   )
        # Tar and untar the tmp_model_folder to /data
        tmp_tar = tar_folder_to_tmpfile(self.tmp_model_folder)
        tmp_container.put_archive("/data", tmp_tar)
        tmp_tar.close()

        # Remove the container - We have sucessfully made a volume with the model folder on.
        return tmp_container.remove()

    def set_keywords(self):
        ## Prepare docker keywords ###
        kw = {}

        ## Full access to ram
        kw["ipc_mode"] = "host"

        # Set input, output and model volumes // see https://docker-py.readthedocs.io/en/stable/containers.html
        kw["volumes"] = {}

        # Mount point of input to container
        kw["volumes"][self.input_folder] = {"bind": self.model["input_mountpoint"],
                                            "mode": "ro"}

        # Mount point of output to container
        kw["volumes"][self.output_folder] = {"bind": self.model["output_mountpoint"],
                                             "mode": "rw"}

        # Mount point of model volume to container if exists
        if self.model["model_available"]:
            kw["volumes"][self.model["model_volume"]] = {"bind": self.model["model_mountpoint"],
                                                         "mode": "ro"}

        # Allow GPU usage if "use_gpu" is True
        if self.model["use_gpu"]:
            kw["device_requests"] = [
                docker.types.DeviceRequest(count=-1, capabilities=[['gpu']])]

    def run(self):
        logging.info(f"{self.task['uid']} Running job!")
        logging.info(f"{self.task['uid']} Task:")
        logging.info(f"{self.task['uid']} {self.task}")
        logging.info(f"{self.task['uid']} Model:")
        logging.info(f"{self.task['uid']} {self.model}")

        try:
            if len(self.kw.keys()) != 0:
                self.cli.containers.run(image=self.model["container_tag"],
                                        command=None,# Already defaults to None, but for explicity
                                        **self.kw)
            else:
                logging.warning("Set keywords with set_keywords() before run()")
        except Exception as e:
            logging.error(e)
