import secrets
import tempfile
import unittest
import uuid
import zipfile
import os
os.environ["LOG_LEVEL"] = "10"

from docker_helper import volume_functions
from docker_helper import docker_volume_exceptions
class TestVolumeFunctions(unittest.TestCase):
    def tearDown(self) -> None:
        for vol in self.to_del:
            try:
                volume_functions.delete_volume(vol)
            except docker_volume_exceptions.VolumeNotFoundException:
                pass

    def setUp(self) -> None:
        self.to_del = []

    def test_create_empty_volume(self):
        volume_id = volume_functions.create_empty_volume()
        self.to_del.append(volume_id)
        self.assertTrue(volume_functions.volume_exists(volume_id=volume_id))

        volume_id = volume_functions.create_empty_volume(str(uuid.uuid4()))
        self.to_del.append(volume_id)
        self.assertTrue(volume_functions.volume_exists(volume_id=volume_id))

    def test_delete_volume(self):
        vol = str(uuid.uuid4())
        self.assertFalse(volume_functions.volume_exists(volume_id=vol))

        echo_vol = volume_functions.create_empty_volume(volume_id=vol)
        self.assertEqual(echo_vol, vol)
        self.assertTrue(volume_functions.volume_exists(volume_id=vol))

        volume_functions.delete_volume(volume_id=vol)
        self.assertFalse(volume_functions.volume_exists(volume_id=vol))

    def test_create_volume_from_tmp_file(self):
        try:
            txt_file = "test.txt"
            with open(txt_file, "w") as f:
                f.write("importent test txt")
            tmp_file = tempfile.TemporaryFile()
            with zipfile.ZipFile(tmp_file, mode="w") as zf:
                zf.write(txt_file)
            tmp_file.seek(0)
            vol_uid = volume_functions.create_volume_from_tmp_file(tmp_file=tmp_file)
            self.assertTrue(volume_functions.volume_exists(volume_id=vol_uid))
        except Exception as e:
            raise e
        finally:
            os.remove(txt_file)
            if tmp_file:
                tmp_file.close()
            volume_functions.delete_volume(vol_uid)

    def test_build_image(self):
        tag = "volume_sender:test"
        if volume_functions.image_exists(tag):
            volume_functions.delete_image(tag, force=True)
        self.assertFalse(volume_functions.image_exists(tag))

        print(volume_functions.build_image(tag=tag, path=os.path.join(os.path.dirname(__file__), "../../volume_sender")))
        self.assertTrue(volume_functions.image_exists(tag))
        volume_functions.delete_image(tag)
        self.assertFalse(volume_functions.image_exists(tag))
