import os
import secrets
import shutil
import tempfile
import unittest
import zipfile

from job.context import volume_context
from docker_helper import volume_functions

class TestVolumeContext(unittest.TestCase):
    def test_create_volume_from_tmp_file(self):
        with tempfile.TemporaryFile() as tmpf:
            with zipfile.ZipFile(tmpf, "w", zipfile.ZIP_DEFLATED) as zipf:
                zipf.writestr("test_file", "This is an impotent test")
            tmpf.seek(0)

            container_id = volume_context.create_volume_from_tmp_file(tmpf)
            self.assertTrue(volume_functions.volume_exists(container_id))
if __name__ == '__main__':
    unittest.main()
