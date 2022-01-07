import unittest
import dotenv
from api_calls import *

dotenv.load_dotenv("/opt/tests/.env")

unittest.TestLoader.sortTestMethodsUsing = lambda *args: -1


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

        self.post_model_res = dict(json.loads(res.content))
        print(self.post_model_res)

        self.assertIn("uid", self.post_model_res.keys())
        self.assertIn("id", self.post_model_res.keys())
        self.model_id = self.post_model_res["id"]
        self.assertEqual(self.post_model_res["container_tag"], self.model_context["container_tag"])
        self.assertEqual(self.post_model_res["input_mountpoint"], self.model_context["input_mountpoint"])
        self.assertEqual(self.post_model_res["output_mountpoint"], self.model_context["output_mountpoint"])
        self.assertEqual(self.post_model_res["model_mountpoint"], self.model_context["model_mountpoint"])


    #  test_get_model_by_id
        model = get_model_by_id(self.post_model_res["id"])

        self.assertEqual(model["id"], self.post_model_res["id"])
        self.assertEqual(model["uid"], self.post_model_res["uid"])
        self.assertEqual(model["container_tag"], self.model_context["container_tag"])
        self.assertEqual(model["input_mountpoint"], self.model_context["input_mountpoint"])
        self.assertEqual(model["output_mountpoint"], self.model_context["output_mountpoint"])
        self.assertEqual(model["model_mountpoint"], self.model_context["model_mountpoint"])

    # test_get_model_by_uid
        model = get_model_by_uid(self.post_model_res["uid"])

        self.assertEqual(model["id"], self.post_model_res["id"])
        self.assertEqual(model["uid"], self.post_model_res["uid"])
        self.assertEqual(model["container_tag"], self.model_context["container_tag"])
        self.assertEqual(model["input_mountpoint"], self.model_context["input_mountpoint"])
        self.assertEqual(model["output_mountpoint"], self.model_context["output_mountpoint"])
        self.assertEqual(model["model_mountpoint"], self.model_context["model_mountpoint"])

    # test_post_task
        input_file = "/data/input.zip"
        with open(input_file, "rb") as r:
            res = post_task_by_model_id(model_id=self.post_model_res["id"], zip_file=r)
        print(res)
        print(res.content)
        task = dict(json.loads(res.content))
        self.assertTrue(res.ok)
        self.assertEqual(task["model_id"], self.post_model_res["id"])
        print(task)

if __name__ == '__main__':
    unittest.main()
