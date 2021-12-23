import argparse
import logging

import uvicorn
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from starlette.middleware import Middleware
from starlette.routing import Host

app = FastAPI()


def main():
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
        with open("tmp", "wb") as f:
            f.write(file.file.read())
        return FileResponse("tmp")
    

    uvicorn.run(app)


if __name__ == "__main__":
    main()
