import _io
import os
import tarfile
import tempfile
import unittest
import zipfile

import dotenv

dotenv.load_dotenv("testing/.env")
from utils.file_handling import zip_folder_to_tmpfile, tar_folder_to_tmpfile


class TestFileHandling(unittest.TestCase):

    def test_zip_folder_to_tmpfile(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            with open(os.path.join(tmp_dir, "tmp_file.txt"), "bw") as f:
                f.write(b"hello hello world")

            with zip_folder_to_tmpfile(tmp_dir) as tmpfile:
                self.assertTrue(isinstance(tmpfile, _io.BufferedRandom))
                z = zipfile.ZipFile(tmpfile, "r")
                self.assertIn("tmp_file.txt", [n.filename for n in z.filelist])

    def test_tar_folder_to_tmpfile(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            with open(os.path.join(tmp_dir, "tmp_file.txt"), "bw") as f:
                f.write(b"hello hello world")

            with tar_folder_to_tmpfile(tmp_dir) as tmpfile:
                self.assertTrue(isinstance(tmpfile, _io.BufferedRandom))
                z = tarfile.TarFile(fileobj=tmpfile)
                self.assertIn("tmp_file.txt", z.getnames()[-1])


if __name__ == '__main__':
    unittest.main()
