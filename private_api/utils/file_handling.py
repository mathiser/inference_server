import logging
import os
import tarfile
import tempfile
import zipfile

LOG_FORMAT = ('%(levelname)s:%(asctime)s:%(message)s')
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)

def unzip_response_to_location(res, dst) -> str:
    # Stream zip to tmp_file
    if not res.ok:
        logging.error(f"RES not ok: {res}")
        return res
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_zip = os.path.join(tmp_dir, "tmp.zip")
        # with open(tmp_zip, "wb") as f:
        #     for chunk in res.iter_content(chunk_size=1024 * 1024 * 10):
        #         f.write(chunk)

        with open(tmp_zip, "wb") as f:
            f.write(res.content)

        with zipfile.ZipFile(file=tmp_zip, mode="r") as zip:
            zip.extractall(path=dst)

    return dst

def zip_folder_to_tmpfile(src) -> zipfile.ZipFile:
    tmp_zip = tempfile.TemporaryFile(suffix=".zip")
    with zipfile.ZipFile(tmp_zip, "w") as zip:
        for file in os.listdir(src):
            zip.write(os.path.join(src, file), arcname=file)
    tmp_zip.seek(0)
    return tmp_zip

def tar_folder_to_tmpfile(src) -> tarfile.TarFile:
    tmp_tar = tempfile.TemporaryFile(suffix=".gzip")
    with tarfile.TarFile(fileobj=tmp_tar, mode="w") as tar:
        tar.add(os.path.abspath(src), arcname=src)
    tmp_tar.seek(0)
    return tmp_tar
