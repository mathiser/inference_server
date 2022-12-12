import unittest
import zipfile
import os
os.environ["LOG_LEVEL"] = "20"

from docker_helper.volume_functions import *

class TestVolumeFunctions(unittest.TestCase):
    def tearDown(self) -> None:
        for vol in self.to_del:
            try:
                delete_volume(vol)
            except VolumeNotFoundException:
                pass

    def setUp(self) -> None:
        self.to_del = []

    def test_create_empty_volume(self):
        volume_id = create_empty_volume()
        self.to_del.append(volume_id)
        self.assertTrue(volume_exists(volume_id=volume_id))

        volume_id = create_empty_volume(secrets.token_urlsafe())
        self.to_del.append(volume_id)
        self.assertTrue(volume_exists(volume_id=volume_id))

    def test_delete_volume(self):
        vol = secrets.token_urlsafe()
        self.assertFalse(volume_exists(volume_id=vol))

        echo_vol = create_empty_volume(volume_id=vol)
        self.assertEqual(echo_vol, vol)
        self.assertTrue(volume_exists(volume_id=vol))

        delete_volume(volume_id=vol)
        self.assertFalse(volume_exists(volume_id=vol))

    def test_create_volume_from_tmp_file(self):
        try:
            txt_file = "test.txt"
            with open(txt_file, "w") as f:
                f.write("importent test txt")
            tmp_file = tempfile.TemporaryFile()
            with zipfile.ZipFile(tmp_file, mode="w") as zf:
                zf.write(txt_file)
            tmp_file.seek(0)
            vol_uid = create_volume_from_tmp_file(tmp_file=tmp_file)
            self.assertTrue(volume_exists(volume_id=vol_uid))
        except Exception as e:
            raise e
        finally:
            os.remove(txt_file)
            if tmp_file:
                tmp_file.close()
            delete_volume(vol_uid)

