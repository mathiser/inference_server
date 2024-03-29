import os
import tarfile
import tempfile
import zipfile
from io import BytesIO


def unzip_tmp_file_to_location(tmp_file: BytesIO, dst: str) -> str:
    with zipfile.ZipFile(file=tmp_file, compression=zipfile.ZIP_DEFLATED) as zip:
        zip.extractall(path=dst)
    return dst


def zip_folder_to_tmpfile(src: str) -> zipfile.ZipFile:
    tmp_zip = tempfile.TemporaryFile(suffix=".zip")
    with zipfile.ZipFile(tmp_zip, "w") as zip:
        for file in os.listdir(src):
            zip.write(os.path.join(src, file), arcname=file)
    tmp_zip.seek(0)
    return tmp_zip


def tar_folder_to_tmpfile(src: str) -> tarfile.TarFile:
    tmp_tar = tempfile.TemporaryFile(suffix=".gzip")
    with tarfile.TarFile(fileobj=tmp_tar, mode="w") as tar:
        tar.add(os.path.abspath(src), arcname=src)
    tmp_tar.seek(0)
    return tmp_tar
