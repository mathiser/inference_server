import traceback
import unittest
import zipfile

import dotenv

dotenv.load_dotenv("testing/.env")
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
        volume_uuid = create_empty_volume()
        self.to_del.append(volume_uuid)
        self.assertTrue(volume_exists(volume_uuid=volume_uuid))

        volume_uuid = create_empty_volume(str(uuid.uuid4()))
        self.to_del.append(volume_uuid)
        self.assertTrue(volume_exists(volume_uuid=volume_uuid))

    def test_delete_volume(self):
        vol = str(uuid.uuid4())
        self.assertFalse(volume_exists(volume_uuid=vol))

        echo_vol = create_empty_volume(volume_uuid=vol)
        self.assertEqual(echo_vol, vol)
        self.assertTrue(volume_exists(volume_uuid=vol))

        delete_volume(volume_uuid=vol)
        self.assertFalse(volume_exists(volume_uuid=vol))

    def test_create_volume_from_tmp_file(self):
        try:
            txt_file = "test.txt"
            with open(txt_file, "w") as f:
                f.write("importent test txt")
            tmp_file = tempfile.TemporaryFile(suffix=".zip")
            with zipfile.ZipFile(tmp_file, "w") as zf:
                zf.write(txt_file)

            vol_uid = create_volume_from_tmp_file(tmp_file=tmp_file)
            self.assertTrue(volume_exists(volume_uuid=vol_uid))
        except Exception as e:
            traceback.print_exc()
            logging.error(e)
        finally:
            os.remove(txt_file)
            if tmp_file:
                tmp_file.close()
            delete_volume(vol_uid)

