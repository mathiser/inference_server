import io
import os
import secrets
import zipfile
import requests

    # Extract uploaded zipfile to input_folder
    with zipfile.ZipFile(io.BytesIO(file.file.read()), "r") as zip:
        zip.extractall(path=input_folder)

    # Inference
    inference = InferenceApp()
    inference.run(input=input_folder, output=output_folder)

    # Zip the output for return
    payload_zip = os.path.join(payload_folder, f"{uid}.zip")
    with zipfile.ZipFile(payload_zip, "w") as zip:
        for file in os.listdir(output_folder):
            zip.write(os.path.join(output_folder, file), file)

    return {"uid": uid}

