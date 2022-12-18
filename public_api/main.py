import os

import uvicorn

from database.db_impl import DBImpl
from database_client.db_client_requests_impl import DBClientRequestsImpl
from public_api.public_api_fast_api_impl import PublicFastAPI

def main():
    db_client = DBClientRequestsImpl(os.environ.get("API_URL"))
    db = DBImpl(db_client=db_client)
    app = PublicFastAPI(db=db)
    uvicorn.run(app=app,
                host="0.0.0.0",
                port=int(os.environ.get("PUBLIC_API_PORT")))

if __name__ == "__main__":
    main()