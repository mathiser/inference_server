import logging
import os
import tarfile
import tempfile
import uuid
from typing import BinaryIO

import docker

from docker_helper.docker_volume_exceptions import VolumeNotFoundException
from utils import file_handling


def create_empty_volume(volume_uuid=None) -> str:
    # Create docker volume named with uid.
    cli = docker.from_env()
    if not volume_uuid:
        volume_uuid = str(uuid.uuid4())
    cli.volumes.create(name=volume_uuid)
    cli.close()

    return volume_uuid


def volume_exists(volume_uuid) -> bool:
    cli = docker.from_env()
    b = (volume_uuid in [v.name for v in cli.volumes.list()])
    cli.close()
    return b


def delete_volume(volume_uuid):
    cli = docker.from_env()
    try:
        return cli.volumes.get(volume_uuid).remove()
    except Exception as e:
        logging.error(e)
        raise VolumeNotFoundException
    finally:
        cli.close()


def create_volume_from_tmp_file(tmp_file: tempfile.TemporaryFile, volume_uuid=None) -> str:
    cli = docker.from_env()
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
        cli.volumes.create(name=volume_uuid)

        # Create a helper container and mount
        cli.images.pull("busybox:1.35")
        tmp_container = cli.containers.create(image="busybox:1.35",
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


def pull_image(container_tag: str):
    cli = docker.from_env()
    cli.images.pull(container_tag)
    cli.close()


if __name__ == "__main__":
    pass
