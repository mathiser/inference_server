import logging
import os
import tarfile
import tempfile
import uuid
from io import BytesIO
from urllib.parse import urljoin

import docker

from docker_helper import volume_functions
from utils import file_handling


def generate_uuid():
    return str(uuid.uuid4())


def create_volume_from_tmp_file(tmp_file: BytesIO, volume_id=None) -> str:
    cli = docker.from_env()
    if not volume_id:
        volume_id = str(uuid.uuid4())

    # Pull_model_zip_and_extract_to_tmp
    # Set a tmp path and create
    try:
        with tempfile.TemporaryDirectory() as tmp_vol_folder:
            vol_dir = os.path.join(tmp_vol_folder, "vol")

            # Stream content to temp file and unzip to tmp_vol_folder
            # Returns the model folder path
            file_handling.unzip_tmp_file_to_location(tmp_file, vol_dir)

            # Create docker volume named with uid.
            cli.volumes.create(name=volume_id)

            # Create a helper container and mount
            cli.images.pull("busybox:1.35")
            tmp_container = cli.containers.create(image="busybox:1.35",
                                                  command=None,
                                                  volumes={volume_id: {"bind": "/data", "mode": "rw"}},
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
        return volume_id

    except Exception as e:
        logging.error(e)
    finally:
        cli.close()


def send_volume(volume_id: str, base_url: str, network_name: str):
    url = urljoin(base_url, "/api/task/output/")
    volume_sender = "volumesender:temp"
    build_volume_sender(tag=volume_sender)
    with docker.from_env() as cli:
        tmp_container = cli.containers.run(volume_sender,
                                           volumes={volume_id: {"bind": '/data', 'mode': 'rw'}},
                                           environment={
                                               "URL": url,
                                               "VOLUME_MOUNTPOINT": "/data"
                                           },
                                           remove=True,
                                           ports={80: []},  ## Dummyport to make traefik shut up
                                           network=network_name)
    return tmp_container


def build_volume_sender(tag):
    p = os.path.abspath("volume_sender")
    return volume_functions.build_image(path=p, tag=tag)
