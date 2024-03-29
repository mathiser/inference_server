import logging
import uuid

import docker


def create_empty_volume(volume_id=None) -> str:
    # Create docker volume named with uid.
    cli = docker.from_env()
    try:
        if not volume_id:
            volume_id = str(uuid.uuid4())

        cli.volumes.create(name=volume_id)

        return volume_id
    except Exception as e:
        logging.error(str(e))
    finally:
        cli.close()


def volume_exists(volume_id) -> bool:
    cli = docker.from_env()
    try:
        b = (volume_id in [v.name for v in cli.volumes.list()])
        return b
    except Exception as e:
        logging.error(str(e))
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
        logging.error(str(e))
    finally:
        cli.close()


def delete_volume(volume_id):
    cli = docker.from_env()
    try:
        return cli.volumes.get(volume_id).remove()
    except Exception as e:
        logging.error(str(e))
    finally:
        cli.close()


def delete_image(tag, force=False):
    cli = docker.from_env()
    try:
        return cli.images.remove(image=tag, force=force)
    except Exception as e:
        logging.error(str(e))
    finally:
        cli.close()


def pull_image(container_tag: str):
    cli = docker.from_env()
    try:
        cli.images.pull(container_tag)
    except Exception as e:
        logging.error(str(e))
    finally:
        cli.close()


if __name__ == "__main__":
    pass
