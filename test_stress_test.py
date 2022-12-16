import logging
import os.path
import random
import secrets
import shutil
import tempfile
import time
import unittest
import zipfile
from io import BytesIO
from multiprocessing.pool import ThreadPool

import docker
import requests

from public_api.interfaces.db_models import Model


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
        os.system(f"docker-compose -f {'test_stack.yaml'} down")
        os.system(f"docker-compose -f test_stack.yaml build")
        os.system(f"docker-compose -f test_stack.yaml up -d")
        time.sleep(5)


    def __del__(self) -> None:
        os.system("docker-compose -f test_stack.yaml logs public_api > public_api_test_log")
        os.system("docker-compose -f test_stack.yaml logs private_api > private_api_test_log")
        os.system("docker-compose -f test_stack.yaml logs consumer > job_consumer_test_log")
        pass


    def test_post_model_private_api(self):
        tag = "mathiser/inference_server_test:pass_through_model"
        human_readable_id = secrets.token_urlsafe(4)
        dockerfile = BytesIO('FROM busybox\nRUN mkdir /input /output /model\nCMD ["cp -r /input/ /output/"]'.encode("utf-8"))
        build_model(tag=tag, dockerfile=dockerfile)

        params = {
            "container_tag": tag,
            "human_readable_id": human_readable_id,
            "model_available": False,
            "use_gpu": False,
            "description": "Testmodel"
        }
        res = requests.post(url="http://localhost:7000/api/models/", params=params)
        self.assertEqual(res.status_code, 200)
        model = Model(**res.json())
        print(model)
        return model

    def test_post_model_public_api(self):
        tag = "mathiser/inference_server_test:pass_through_model"
        human_readable_id = secrets.token_urlsafe(4)
        dockerfile = BytesIO('FROM busybox\nRUN mkdir /input /output /model\nCMD cp -r /input/* /output/'.encode("utf-8"))
        build_model(tag=tag, dockerfile=dockerfile)
        params = {
            "container_tag": tag,
            "human_readable_id": human_readable_id,
            "model_available": False,
            "use_gpu": False,
            "description": "Testmodel"
        }
        res = requests.post(url="http://localhost:8000/api/models/", params=params)
        print(res.json())
        self.assertEqual(res.status_code, 200)
        model = Model(**res.json())
        print(model)
        return model

    def test_get_models_public_api(self):
        self.test_post_model_private_api()
        self.test_post_model_private_api()

        ress = requests.get(url="http://localhost:8000/api/models/")
        models = [Model(**res) for res in ress.json()]
        print(models)
        self.assertEqual(ress.status_code, 200)
        return models

    def test_post_task(self, model=None):
        if not model:
            model = self.test_post_model_public_api()
            with self.make_temp_zip_file() as r:
                res = requests.post("http://localhost:8000/api/tasks/",
                                params={"model_human_readable_id": model.human_readable_id},
                                files={"zip_file": r})
                res.raise_for_status()
                return res.json(), r.read()

    def test_get_output_zip(self, uid=None):
        compare = False
        if not uid:
            compare = True
            uid, content = self.test_post_task()
            with zipfile.ZipFile(BytesIO(content)) as zf:
                ref_list = [z.filename for z in zf.filelist]

        while True:
            res = requests.get(f"http://localhost:8000/api/tasks/outputs/{uid}")
            if res.ok:
                with zipfile.ZipFile(BytesIO(res.content)) as zf_res:
                    ref_res = [z.filename for z in zf_res.filelist]
                    if compare:
                        self.assertListEqual(ref_list, ref_res)
            else:
                time.sleep(5)

    def test_stress_test(self, n_models=10, n_tasks=10, n_threads=1):
        models = [self.test_post_model_public_api() for n in range(n_models)]
        t = ThreadPool(n_threads)
        results = t.map(self.test_post_task, [random.choice(models) for n in range(n_tasks)])
        t.close()
        t.join()
        uids = [result[0] for result in results]

        t = ThreadPool(n_tasks)
        results = t.map(self.test_get_output_zip, uids)
        t.close()
        t.join()
        print(results)

    def test_post_model_with_zip_public_api(self):
        tag = "mathiser/inference_server_test:pass_through_model_with_model_zip"
        human_readable_id = secrets.token_urlsafe(4)
        dockerfile = BytesIO('FROM busybox\nRUN mkdir /input /output /model\nCMD cp -r /model/* /output/'.encode("utf-8"))
        build_model(tag=tag, dockerfile=dockerfile)
        params = {
            "container_tag": tag,
            "human_readable_id": human_readable_id,
            "model_available": True,
            "use_gpu": False,
            "description": "Testmodel"
        }
        with self.make_temp_zip_file() as f:
            res = requests.post(url="http://localhost:8000/api/models/", params=params, files={"zip_file": f})

        self.assertEqual(res.status_code, 200)
        model = Model(**res.json())
        models = self.test_get_models_public_api()
        self.assertIn(model.uid, [m.uid for m in models])
        return model

    def make_temp_zip_file(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            with open(os.path.join(tmp_dir, "test1.txt"), "w") as f:
                f.write("Veri secure and important file to me zipped.")
            os.makedirs(os.path.join(tmp_dir, "0", "1", "2"))
            with open(os.path.join(tmp_dir, "0", "1", "2", "test2.txt"), "w") as f:
                f.write("another veri secure and important file to me zipped.")

            temp_file = tempfile.TemporaryFile()
            with zipfile.ZipFile(temp_file, mode="w") as zf:
                for fol, subs, files in os.walk(tmp_dir):
                    for file in files:
                        zf.write(filename=os.path.join(fol, file), arcname=file)
            temp_file.seek(0)
            return temp_file

if __name__ == '__main__':
    unittest.main()
