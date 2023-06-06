import os.path
import secrets
import tempfile
import time
import unittest
import tarfile
from io import BytesIO

import docker
import requests


def build_model(tag, dockerfile):
    cli = docker.from_env()
    try:
        if not tag in [container.name for container in cli.containers.list()]:
            cli.images.build(fileobj=dockerfile, tag=tag)
    except Exception as e:
        raise e
    finally:
        cli.close()

class TestEndToEnd(unittest.TestCase):
    path = os.path.dirname(os.path.abspath(__file__))

    def setUp(self) -> None:
        self.INFERENCE_SERVER_TOKEN="test-hest"

    def __del__(self) -> None:
        os.system("docker compose logs controller > controller.log")
        os.system("docker compose logs consumer > consumer.log")

    def test_post_model(self):
        tag = "mathiser/inference_server_test:pass_through_model"
        human_readable_id = secrets.token_urlsafe(4)
        dockerfile = BytesIO(
            'FROM busybox\nRUN mkdir /input /output /model\nCMD ["cp -r /input/ /output/"]'.encode("utf-8"))
        build_model(tag=tag, dockerfile=dockerfile)

        params = {
            "container_tag": tag,
            "human_readable_id": human_readable_id,
            "model_available": False,
            "use_gpu": False,
            "description": "Testmodel"
        }
        res = requests.post(url="http://localhost:8123/api/models/",
                            params=params,
                            headers={"X-Token": self.INFERENCE_SERVER_TOKEN})
        self.assertEqual(res.status_code, 200)
        model = res.json()
        print(model)
        return model

    def test_get_models(self):
        self.test_post_model()
        self.test_post_model()

        ress = requests.get(url="http://localhost:8123/api/models/",
                            headers={"X-Token": self.INFERENCE_SERVER_TOKEN})
        models = ress.json()
        print(models)
        self.assertEqual(200, ress.status_code)
        return models

    def test_post_task(self, model=None):
        if not model:
            model = self.test_post_model()
            with self.make_temp_tar_file() as r:
                res = requests.post("http://localhost:8123/api/tasks/",
                                    params={"human_readable_id": model["human_readable_id"]},
                                    files={"tar_file": r})
                res.raise_for_status()
                r.seek(0)
                return res.json(), r.read()

    def test_get_output_tar(self, uid=None):
        compare = False
        if not uid:
            compare = True
            uid, content = self.test_post_task()
            with tarfile.TarFile.open(fileobj=BytesIO(content), mode="r") as zf:
                ref_list = [member.path for member in zf.getmembers()]

        counter = 0
        while counter < 10:
            res = requests.get(f"http://localhost:8123/api/tasks/outputs/",
                               params={"uid": uid})
            if res.ok:
                with tarfile.TarFile.open(fileobj=BytesIO(res.content), mode="w|gz") as zf_res:
                    ref_res = [member.path for member in zf_res.getmembers()]
                    if compare:
                        self.assertListEqual(ref_list, ref_res)
                        return
            else:
                time.sleep(5)
                counter += 1
                
    def test_model_tar(self):
        model = self.test_post_model_with_tar()
        uid = self.test_post_task(model=model)
        self.test_get_output_tar(uid=uid)

    def test_post_model_with_tar(self):
        tag = "mathiser/inference_server_test:pass_through_model_with_model_tar"
        human_readable_id = secrets.token_urlsafe(4)
        dockerfile = BytesIO(
            'FROM busybox\nRUN mkdir /input /output /model\nCMD cp -r /model/* /output/'.encode("utf-8"))
        build_model(tag=tag, dockerfile=dockerfile)
        params = {
            "container_tag": tag,
            "human_readable_id": human_readable_id,
            "model_available": True,
            "use_gpu": False,
            "description": "Testmodel"
        }
        with self.make_temp_tar_file() as f:
            res = requests.post(url="http://localhost:8123/api/models/", params=params, files={"tar_file": f},
                                headers={"X-Token": self.INFERENCE_SERVER_TOKEN})

        self.assertEqual(res.status_code, 200)
        model = res.json()
        models = self.test_get_models()
        self.assertIn(model["id"], [m["id"] for m in models])
        return model

    @staticmethod
    def make_temp_tar_file():
        with tempfile.TemporaryDirectory() as tmp_dir:
            with open(os.path.join(tmp_dir, "test1.txt"), "w") as f:
                f.write("Veri secure and important file to me tarped.")
            os.makedirs(os.path.join(tmp_dir, "0", "1", "2"))
            with open(os.path.join(tmp_dir, "0", "1", "2", "test2.txt"), "w") as f:
                f.write("another veri secure and important file to me tarped.")

            temp_file = tempfile.TemporaryFile()
            with tarfile.TarFile.open(fileobj=temp_file, mode="w|gz") as zf:
                for fol, subs, files in os.walk(tmp_dir):
                    for file in files:
                        zf.add(os.path.join(fol, file), arcname=file)
            temp_file.seek(0)
            return temp_file


if __name__ == '__main__':
    #TestEndToEnd.make_temp_tar_file()
    unittest.main()
