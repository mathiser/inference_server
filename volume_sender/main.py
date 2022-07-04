import os
import tempfile
import zipfile
import logging
import requests

LOG_FORMAT = ('%(levelname)s:%(asctime)s:%(message)s')
logging.basicConfig(level=int(os.environ.get("LOG_LEVEL")), format=LOG_FORMAT)

def zip_folder_to_tmpfile(src) -> zipfile.ZipFile:
    print(os.listdir(src))
    if len(os.listdir(src)) == 0:
        with open(os.path.join(src, "no_output_files_found.error"), "w") as f:
            f.write("This is a dummyfile")

    tmp_zip = tempfile.TemporaryFile(suffix=".zip")
    with zipfile.ZipFile(tmp_zip, "w") as zip:
        for file in os.listdir(src):
            zip.write(os.path.join(src, file), arcname=file)
    tmp_zip.seek(0)
    return tmp_zip


def main():
    tmp_zip = zip_folder_to_tmpfile(os.environ.get("VOLUME_MOUNTPOINT"))
    res = requests.post(os.environ.get("URL"), files={"zip_file": tmp_zip})
    print(res)

    tmp_zip.close()
    return res

if __name__ == "__main__":
    main()