import logging
import os
import uuid

import docker

from api_calls import *
from file_handling import *

LOG_FORMAT = ('%(levelname)s:%(asctime)s:%(message)s')
logging.basicConfig(level=logging.DEBUG, format=LOG_FORMAT)


class DockerHandler:
    def __init__(self, input_volume_uuid, output_volume_uuid, model, task):
        self.input_volume_uuid = input_volume_uuid
        self.output_volume_uuid = output_volume_uuid
        self.model = model
        self.model_volume_uuid = self.model["model_volume"]
        self.task = task
        self.cli = docker.from_env()
        self.kw = {}

        # Set keywords for container
        self.set_keywords()

        ## Check if model exists, else pull and create volume:

        if not DockerVolumeHandler().volume_exists(self.input_volume_uuid):
            logging.info("Model volume does not exit. Pulling from db and creating")
            raise Exception("Input volume does not exist while it should")

        if self.model["model_available"]:
            if not DockerVolumeHandler().volume_exists(self.model_volume_uuid):
                raise Exception("Model volume does not exist while it should")

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
        logging.info(f"{self.task['uid']} Running job!")
        logging.info(f"{self.task['uid']} Task:")
        logging.info(f"{self.task['uid']} {self.task}")
        logging.info(f"{self.task['uid']} Model:")
        logging.info(f"{self.task['uid']} {self.model}")
        logging.info(f"{self.task['uid']} Keywords:")
        logging.info(f"{self.task['uid']} {self.kw}")

        try:
            tmp_container = self.cli.containers.run(image=self.model["container_tag"],
                                    command=None,  # Already defaults to None, but for explicity
                                    **self.kw)
            logging.info(tmp_container)
        except Exception as e:
            logging.error(e)

    def close(self):
        self.cli.close()

class DockerVolumeHandler:
    @staticmethod
    def volume_exists(uuid):
        cli = docker.from_env()
        b = uuid in [v.name for v in cli.volumes.list()]
        cli.close()

        return b
    @staticmethod
    def create_volume_from_response(res, volume_uuid=str(uuid.uuid4())):
        cli = docker.from_env()

        # Pull_model_zip_and_extract_to_tmp
        # Set a tmp path and create
        with tempfile.TemporaryDirectory() as tmp_vol_folder:
            vol_dir = os.path.join(tmp_vol_folder, "vol")

            # Stream content to temp file and unzip to tmp_vol_folder
            # Returns the model folder path
            unzip_response_to_location(res, vol_dir)

            # Create docker volume named with uid.
            cli.volumes.create(name=volume_uuid)

            # Create a helper container and mount
            tmp_container = cli.containers.create(image="busybox",
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
        cli.close()
        return volume_uuid

    @staticmethod
    def delete_volume(uuid):
        cli = docker.from_env()
        res = cli.volumes.get(uuid).remove()
        cli.close()
        return res
    @staticmethod
    def send_volume(volume_uuid, url):
        cli = docker.from_env()
        logging.info("URL to post on: {}".format(url))
        tmp_container = cli.containers.run("mathiser/inference_server:volume_sender",
                                       None,
                                       volumes={volume_uuid: {"bind": '/data', 'mode': 'ro'}},
                                       environment={
                                           "URL": url,
                                           "VOLUME_MOUNTPOINT": "/data"
                                       },
                                       remove=True,
                                       network=os.environ.get("NETWORK_NAME"))
        logging.info(tmp_container)
        cli.close()
