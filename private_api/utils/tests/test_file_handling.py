import _io
import logging
import os
import secrets
import tarfile
import tempfile
import unittest
import zipfile

import requests

from utils.file_handling import unzip_response_to_location, zip_folder_to_tmpfile, tar_folder_to_tmpfile


class TestFileHandling(unittest.TestCase):
    def test_unzip_response_to_location(self):
        res = requests.Response()
        with tempfile.TemporaryDirectory() as tmp_dir:
            with open(os.path.join(tmp_dir, "tmp_file.txt"), "bw") as f:
                f.write(b"hello hello world")

            with zipfile.ZipFile(os.path.join(tmp_dir, "tmp_file.zip"), "w") as f:
                f.write(os.path.join(tmp_dir, "tmp_file.txt"), arcname="tmp_file.txt")

            with open(os.path.join(tmp_dir, "tmp_file.zip"), "br") as r:
                res._content = r.read()
                res.status_code = 200

        with tempfile.TemporaryDirectory() as tmp_dir:
            unzip_response_to_location(res, tmp_dir)

            self.assertEqual(len(os.listdir(tmp_dir)), 1)
            self.assertEqual(os.listdir(tmp_dir)[0], "tmp_file.txt")
            with open(os.path.join(tmp_dir, "tmp_file.txt"), "br") as r:
                self.assertEqual(b"hello hello world", r.read())

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
