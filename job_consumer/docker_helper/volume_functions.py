import logging
import os
import secrets
import tarfile
import tempfile
import uuid

import docker
from docker.models.images import Image

from utils import file_handling


def create_empty_volume(volume_id=None) -> str:
    # Create docker volume named with uid.
    cli = docker.from_env()
    try:
        if not volume_id:
            volume_id = str(uuid.uuid4())

        cli.volumes.create(name=volume_id)

        return volume_id
    except Exception as e:
        logging.error(e)
    finally:
        cli.close()


def volume_exists(volume_id) -> bool:
    cli = docker.from_env()
    try:
        b = (volume_id in [v.name for v in cli.volumes.list()])
        return b
    except Exception as e:
        logging.error(e)
    finally:
        cli.close()


def image_exists(tag) -> bool:
    cli = docker.from_env()
    try:
        for image in cli.images.list():
            if tag in image.tags:
                return True
        else:
            return False
    except Exception as e:
        logging.error(e)
    finally:
        cli.close()


def delete_volume(volume_id):
    cli = docker.from_env()
    try:
        return cli.volumes.get(volume_id).remove()
    except Exception as e:
        logging.error(e)
    finally:
        cli.close()


def delete_image(tag, force=False):
    cli = docker.from_env()
    try:
        return cli.images.remove(image=tag, force=force)
    except Exception as e:
        logging.error(e)
    finally:
        cli.close()


def build_image(tag, path):
    cli = docker.from_env()
    if not os.path.exists(path):
        print(f"Path does not exist. Looking from {os.getcwd()}")
        raise Exception(f"Path does not exist. Looking from {os.getcwd()}")
    try:
        return cli.images.build(path=path,
                                tag=tag)
    except Exception as e:
        logging.error(e)
        raise e
    finally:
        cli.close()


def create_volume_from_tmp_file(tmp_file: tempfile.TemporaryFile, volume_id=None) -> str:
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


def pull_image(container_tag: str):
    cli = docker.from_env()
    try:
        cli.images.pull(container_tag)
    except Exception as e:
        logging.error(e)
    finally:
        cli.close()


if __name__ == "__main__":
    pass
