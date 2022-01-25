import logging
import os
import tarfile
import tempfile
import uuid

import docker

from .file_handling import unzip_response_to_location


def volume_exists(uuid):
    cli = docker.from_env()
    b = uuid in [v.name for v in cli.volumes.list()]
    cli.close()

    return b

def create_volume_from_response(res, volume_uuid=None):
    cli = docker.from_env()

    if not volume_uuid:
        volume_uuid = str(uuid.uuid4())

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

def create_empty_volume():
    cli = docker.from_env()
    # Create docker volume named with uid.
    volume_uuid = str(uuid.uuid4())
    cli.volumes.create(name=volume_uuid)
    cli.close()
    return volume_uuid

def delete_volume(uuid):
    cli = docker.from_env()
    res = cli.volumes.get(uuid).remove()
    cli.close()
    return res

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