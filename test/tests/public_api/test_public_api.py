import os
import time
import unittest
from urllib.parse import urljoin

import dotenv
import requests
dotenv.load_dotenv("/opt/tests/pub_api_paths")
import json
unittest.TestLoader.sortTestMethodsUsing = lambda *args: -1
global task_context, post_model_res, task


class TestPublicAPIModelAndInputs(unittest.TestCase):
    def setUp(self):
        self.api_url = os.environ.get("PUBLIC_API_URL")
        self.model_context = {
            "container_tag": "mathiser/nnunet:5003_wholeheart",
            "input_mountpoint": "/input",
            "output_mountpoint": "/output",
            "model_mountpoint": "/model",
            "file_zip": "/data/model.zip"
        }

    def test_pub_post_model_api(self):
        # Post a model
        with open(self.model_context["file_zip"], "rb") as r:
            params = {
                "container_tag": self.model_context["container_tag"],
                "input_mountpoint": self.model_context["input_mountpoint"],
                "output_mountpoint": self.model_context["output_mountpoint"],
                "model_mountpoint": self.model_context["model_mountpoint"],
                "model_available": True,
                "use_gpu": True
            }
            res = requests.post(os.environ["PUBLIC_API_URL"] + os.environ["PUBLIC_POST_MODEL"], params=params,
                                files={"zip_file": r})

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

    def test_public_post_task(self):
        global post_model_res, task
        input_file = "/data/input.zip"
        with open(input_file, "rb") as r:
            res = requests.post(os.environ["PUBLIC_API_URL"] + urljoin(os.environ["PUBLIC_POST_TASK_BY_MODEL_ID"], str(self.model_context["id"])),
                                    files={"zip_file": r})

        print(res)
        print(res.content)

        task = dict(json.loads(res.content))
        self.assertTrue(res.ok)
        print(task)

    def test_get_output(self):
        global task
        os.makedirs(f"/data/{task['uid']}")
        counter = 0
        while True:
            res = requests.get(os.environ["PUBLIC_API_URL"] + urljoin(os.environ["PUBLIC_GET_OUTPUT_ZIP_BY_UID"],
                               task["uid"]),
                               stream=True)

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
