import os
import tempfile
import zipfile


def unzip_response_to_location(res, dst):
    if not os.path.exists(dst):
        os.makedirs(dst)

    # Request get image_zip from DB
    with tempfile.TemporaryFile() as tmp_input_zip:
        tmp_input_zip.write(res.content)

        # Extract input zipfile to input_folder
        with zipfile.ZipFile(tmp_input_zip, "r") as zip:
            zip.extractall(path=dst)

    return dst

def zip_folder_to_tmpfile(src):
    with tempfile.TemporaryFile() as tmp_output_zip:
        with zipfile.ZipFile(tmp_output_zip, "w") as zip:
            for file in os.listdir(src):
                zip.write(os.path.join(src, file), arcname=file)
    return tmp_output_zip