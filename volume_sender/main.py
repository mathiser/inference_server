import os
import tempfile
import zipfile
from urllib.parse import urljoin

import requests


def zip_folder_to_tmpfile(src) -> zipfile.ZipFile:
    tmp_zip = tempfile.TemporaryFile(suffix=".zip")
    with zipfile.ZipFile(tmp_zip, "w") as zip:
        for file in os.listdir(src):
            zip.write(os.path.join(src, file), arcname=file)
    tmp_zip.seek(0)
    return tmp_zip


def main():
    tmp_zip = zip_folder_to_tmpfile(os.environ.get("VOLUME_MOUNTPOINT"))
    res = requests.post(os.environ.get("URL"), files={"zip_file": tmp_zip})
    tmp_zip.close()
    return res

if __name__ == "__main__":
    main()