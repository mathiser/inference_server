import io
import os
import secrets
import zipfile

import uvicorn
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import FileResponse
from app.nnunet_inference_app import InferenceApp

app = FastAPI()

@app.get("/")
def hello_world():
    return {"message": "Hello world!"}

@app.post("/upload/")
def upload_file(file: UploadFile = File(...)):
    """Defines REST POST Endpoint for Uploading input payloads.
    Will trigger inference job sequentially after uploading payload

    Args:
        file (UploadFile, optional): .zip file provided by user to be moved
        and extracted in shared volume directory for input payloads. Defaults to File(...).

    Returns:
        FileResponse: Asynchronous object for FastAPI to stream compressed .zip folder with
        the output payload from running the MONAI Application Package
    """

    # Local place to save images and predictions
    image_folder = "/opt/app/data/images"
    prediction_folder = "/opt/app/data/predictions"
    payload_folder = "/opt/app/data/payloads"

    # Give this request a unique identifier
    uid = secrets.token_urlsafe(32)

    # Define input folder and output folder for inference
    input_folder = os.path.join(image_folder, uid)
    output_folder = os.path.join(prediction_folder, uid)

    # Create folders
    for p in [input_folder, output_folder, payload_folder]:
        if not os.path.exists(p):
            os.makedirs(p)

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

    return FileResponse(payload_zip)

