import os
import time
import unittest
import dotenv
from api_calls import *

dotenv.load_dotenv("/opt/tests/private_api_paths")

unittest.TestLoader.sortTestMethodsUsing = lambda *args: -1
global task_context, post_model_res, task


class TestModelAndInputsAPI(unittest.TestCase):
    def setUp(self):
        self.api_url = os.environ.get("API_URL")
        self.model_context = {
            "container_tag": "mathiser/nnunet:5003_wholeheart",
            "input_mountpoint": "/input",
            "output_mountpoint": "/output",
            "model_mountpoint": "/model",
            "file_zip": "/data/model.zip"
        }

    def test_private_api(self):
        # Post a model
        with open(self.model_context["file_zip"], "rb") as r:
            res = post_model(
                container_tag=self.model_context["container_tag"],
                input_mountpoint=self.model_context["input_mountpoint"],
                output_mountpoint=self.model_context["output_mountpoint"],
                model_mountpoint=self.model_context["model_mountpoint"],
                zip_file=r,
                model_available=True,
                use_gpu=True
               )
        print(res)
        print(res.content)
        self.assertTrue(res.ok)

        global post_model_res
        post_model_res = dict(json.loads(res.content))
        print(post_model_res)

        self.assertIn("uid", post_model_res.keys())
        self.assertIn("id", post_model_res.keys())
        self.assertEqual(post_model_res["container_tag"], self.model_context["container_tag"])
        self.assertEqual(post_model_res["input_mountpoint"], self.model_context["input_mountpoint"])
        self.assertEqual(post_model_res["output_mountpoint"], self.model_context["output_mountpoint"])
        self.assertEqual(post_model_res["model_mountpoint"], self.model_context["model_mountpoint"])


    def test_get_model_by_id(self):
        global post_model_res
        model = get_model_by_id(post_model_res["id"])

        self.assertEqual(model["id"], post_model_res["id"])
        self.assertEqual(model["uid"], post_model_res["uid"])
        self.assertEqual(model["container_tag"], self.model_context["container_tag"])
        self.assertEqual(model["input_mountpoint"], self.model_context["input_mountpoint"])
        self.assertEqual(model["output_mountpoint"], self.model_context["output_mountpoint"])
        self.assertEqual(model["model_mountpoint"], self.model_context["model_mountpoint"])

    def test_get_model_by_uid(self):
        global post_model_res
        model = get_model_by_uid(post_model_res["uid"])

        self.assertEqual(model["id"], post_model_res["id"])
        self.assertEqual(model["uid"], post_model_res["uid"])
        self.assertEqual(model["container_tag"], self.model_context["container_tag"])
        self.assertEqual(model["input_mountpoint"], self.model_context["input_mountpoint"])
        self.assertEqual(model["output_mountpoint"], self.model_context["output_mountpoint"])
        self.assertEqual(model["model_mountpoint"], self.model_context["model_mountpoint"])

    def test_post_task(self):
        global post_model_res, task
        input_file = "/data/input.zip"
        with open(input_file, "rb") as r:
            res = post_task_by_model_id(model_id=post_model_res["id"], zip_file=r)
        print(res)
        print(res.content)

        task = dict(json.loads(res.content))
        self.assertTrue(res.ok)
        self.assertEqual(task["model_id"], post_model_res["id"])
        print(task)

    def test_get_output(self):
        global task
        os.makedirs(f"/data/{task['uid']}")
        counter = 0
        while True:
            res = get_output_zip_by_uid(task["uid"])
            if res.ok:
                with open(f"/data/{task['uid']}/output.zip", "wb") as f:
                    for chunk in res.iter_content(chunk_size=1000000):
                        f.write(chunk)
                break
            else:
                time.sleep(5)
                counter += 5
                print("sleeeeping ... slep for {} seconde".format(counter))

if __name__ == '__main__':
    unittest.main()
