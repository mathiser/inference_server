import os
import time
import unittest
from urllib.parse import urljoin

import dotenv
import requests
dotenv.load_dotenv("/opt/tests/pub_api_paths")
import json
import certifi

verify = os.environ.get("CERT_FILE")
print(verify)

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
class TestPublicAPIModelAndInputs(unittest.TestCase):
    def test_hello_world(self):
        res = requests.get(os.environ.get("PROXY_URL"), verify=verify)
        self.assertTrue(res)
        print(res.content)

    def test0_pub_get_model_api(self):
        global holder

        res = requests.post(os.environ.get("PROXY_URL") + os.environ["PUBLIC_GET_MODELS"])
        print(f"res: {res}")
        print(res.content)
        self.assertTrue(res.ok)

        holder.post_model_res = json.loads(res.content)
        print(holder.post_model_res)

    def test1_public_post_task(self):
        global holder
        print("def test_public_post_task(self):")
        input_file = "/data/input.zip"
        with open(input_file, "rb") as r:
            url = os.environ.get("PROXY_URL") + urljoin(os.environ["PUBLIC_POST_TASK_BY_MODEL_ID"], str(holder.post_model_res["id"]))
            print(f"Posting on {url}")
            res = requests.post(url,
                                files={"zip_file": r},
                                verify=verify)
        self.assertTrue(res.ok)

        print(res)
        print(res.content)
        holder.task = dict(json.loads(res.content))
        print(f"Task: {holder.task}")

    def test2_get_output(self):
        global holder
        print("def test_get_output(self):")
        os.makedirs(f"/data/{holder.task['uid']}")
        counter = 0
        while True:
            res = requests.get(os.environ.get("PROXY_URL") + urljoin(os.environ["PUBLIC_GET_OUTPUT_ZIP_BY_UID"],
                               holder.task["uid"]),
                               stream=True,
                               verify=verify)

            if res.ok:
                with open(f"/data/{holder.task['uid']}/output.zip", "wb") as f:
                    for chunk in res.iter_content(chunk_size=1000000):
                        f.write(chunk)
                break
            else:
                time.sleep(5)
                counter += 5
                print("sleeeeping ... slept for {} seconds".format(counter))


if __name__ == '__main__':

    unittest.main()
