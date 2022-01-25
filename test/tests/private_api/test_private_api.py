import json
import os
import time
import unittest
import dotenv
from api_calls import *
import requests

dotenv.load_dotenv("/opt/tests/private_api_paths")

class Holder:
    def __init__(self):
        self.model_context = None
        self.post_model_res = None
        self.task = None

holder = Holder()
holder.model_context = {
    "container_tag": "mathiser/nnunet:5003_wholeheart",
    "input_mountpoint": "/input",
    "output_mountpoint": "/output",
    "model_mountpoint": "/model",
    "file_zip": "/data/model.zip"
}

unittest.TestLoader.sortTestMethodsUsing = None

class TestModelAndInputsAPI(unittest.TestCase):
    def test0_private_api(self):

        print("def test_private_api(self):")
        # Post a model
        with open(holder.model_context["file_zip"], "rb") as r:
            res = post_model(
                container_tag=holder.model_context["container_tag"],
                input_mountpoint=holder.model_context["input_mountpoint"],
                output_mountpoint=holder.model_context["output_mountpoint"],
                model_mountpoint=holder.model_context["model_mountpoint"],
                zip_file=r,
                model_available=True,
                use_gpu=True
               )
        print(res)
        print(res.content)
        self.assertTrue(res.ok)

        holder.post_model_res = dict(json.loads(res.content))
        print(holder.post_model_res)

        self.assertIn("id", holder.post_model_res.keys())
        self.assertEqual(holder.post_model_res["container_tag"], holder.model_context["container_tag"])
        self.assertEqual(holder.post_model_res["input_mountpoint"], holder.model_context["input_mountpoint"])
        self.assertEqual(holder.post_model_res["output_mountpoint"], holder.model_context["output_mountpoint"])
        self.assertEqual(holder.post_model_res["model_mountpoint"], holder.model_context["model_mountpoint"])


    def test1_get_model_by_id(self):
        print("def test_get_model_by_id(self):")
        global holder
        model = get_model_by_id(holder.post_model_res["id"])

        self.assertEqual(model["id"], holder.post_model_res["id"])
        self.assertEqual(model["container_tag"], holder.model_context["container_tag"])
        self.assertEqual(model["input_mountpoint"], holder.model_context["input_mountpoint"])
        self.assertEqual(model["output_mountpoint"], holder.model_context["output_mountpoint"])
        self.assertEqual(model["model_mountpoint"], holder.model_context["model_mountpoint"])

    def test2_post_task(self):
        print("def test_post_task(self):")
        global holder
        input_file = "/data/input.zip"
        models_list = [int(holder.post_model_res["id"])]
        params = {
            "models": models_list,
        }
        with open(input_file, "rb") as r:
            res = requests.post(os.environ["API_URL"] + os.environ["POST_TASK"],
                                files={"zip_file": r}, params=params)
        print(res)
        print(res.content)

        holder.task = dict(json.loads(res.content))
        self.assertTrue(res.ok)
        print(holder.task)

    def test3_get_output(self):
        print("def test_get_output(self):")
        os.makedirs(f"/data/outputs/{holder.task['uid']}")
        counter = 0
        while True:
            res = get_output_zip_by_uid(holder.task["uid"])
            if res.ok:
                with open(f"/data/outputs/{holder.task['uid']}/output.zip", "wb") as f:
                    for chunk in res.iter_content(chunk_size=1000000):
                        f.write(chunk)
                break
            else:
                time.sleep(1)
                counter += 1
                print("sleeeeping ... slept for {} seconds".format(counter))

if __name__ == '__main__':
    unittest.main()
