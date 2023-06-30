import logging
import os
import tarfile
import tempfile
import traceback
import uuid
from io import BytesIO
from typing import Dict, Union

import docker
from docker import types
from docker.models.containers import Container

from docker_helper import volume_functions
from database.db_models import Task


def extract_tar_to_container_path(container: Container, tar: bytes, path: str):
    return container.put_archive(path, tar)
 

def exec_job(task: Task, input_tar: BytesIO, model_tar: BytesIO, pull_on_every_run: bool, dump_logs: bool, gpu_uuid: Union[str, None] = None):
    try:
        cli = docker.from_env()
        if pull_on_every_run or not volume_functions.image_exists(task.model.container_tag):
            volume_functions.pull_image(task.model.container_tag)
        container = cli.containers.create(image=task.model.container_tag,
                                              command=None,  # Already defaults to None, but for explicity
                                              ports={80: []},  # Dummy port to make traefik shut up
                                              **generate_keywords(task=task, gpu_uuid=gpu_uuid),
                                            )
        container.put_archive("/input/", input_tar)

        if model_tar:
            container.put_archive("/model/", model_tar)

        container.start()
        container.wait() # Blocks...

        # Grab /output
        output_tar, stats = container.get_archive(path="/output")
        output = BytesIO()
        for chunck in output_tar:
            output.write(chunck)
        output.seek(0)

        output_tar = postprocess_output_tar(tarf=output, logs=container.logs(), dump_logs=dump_logs)

        return output_tar

    except Exception as e:
        logging.error(str(e))
        print(traceback.format_exc())
        container.remove(force=True)
        container.client.close()
        raise e


def postprocess_output_tar(tarf: BytesIO, logs: str, dump_logs: bool):
    """
    Removes one layer from the output_tar - i.e. the /output/
    If dump_logs==True, container logs are dumped to container.log
    """
    container_tar_obj = tarfile.TarFile.open(fileobj=tarf, mode="r|*")

    # Unwrap container tar to temp dir
    with tempfile.TemporaryDirectory() as tmpd:
        container_tar_obj.extractall(tmpd)
        container_tar_obj.close()

        # Make a new temp tar.gz
        new_tar_file = BytesIO()
        new_tar_obj = tarfile.TarFile.open(fileobj=new_tar_file, mode="w")

        # Walk directory from output to strip it away
        for fol, subs, files in os.walk(os.path.join(tmpd, "output")):
            for file in files:
                new_tar_obj.add(os.path.join(fol, file), arcname=file)

        if dump_logs:
            new_tar_obj.addfile(tarfile.TarInfo("container.log"), fileobj=BytesIO(logs))

    new_tar_obj.close()  # Now safe to close tar obj
    new_tar_file.seek(0)  # Reset pointer
    return new_tar_file  # Ready to ship directly to DB

def generate_keywords(task, gpu_uuid) -> Dict:
    ## Prepare docker keywords ###
    kw = {}

    ## Full access to ram
    kw["ipc_mode"] = "host"

    # Set input, output and model volumes // see https://docker-py.readthedocs.io/en/stable/containers.html
    kw["volumes"] = {}

    # Mount point of input/output to container. These are dummy binds, to make sure the container has /input and /output
    kw["volumes"][tempfile.mkdtemp(dir="/tmp/")] = {"bind": "/input",
                                            "mode": "rw"}
    kw["volumes"][tempfile.mkdtemp(dir="/tmp/")] = {"bind": "/output",
                                            "mode": "rw"}

    # Mount point of model volume to container if exists
    if task.model.model_available:
        kw["volumes"][task.model.model_volume_id] = {"bind": "/model",
                                                     "mode": "rw"}

    # Allow GPU usage if "use_gpu" is True
    if task.model.use_gpu:
        logging.info(f"GPU UUID: {gpu_uuid}")
        if not gpu_uuid:
            kw["device_requests"] = [
                docker.types.DeviceRequest(count=-1, capabilities=[['gpu']])]
        else:
            kw["device_requests"] = [
                docker.types.DeviceRequest(device_ids=[gpu_uuid], capabilities=[['gpu']])]

    logging.debug(str(kw))
    return kw

