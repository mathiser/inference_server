import os

import dotenv
import uvicorn

from database.db_requests_impl import DBRequestsImpl
from database_client.db_client_requests_impl import DBClientRequestsImpl
from public_api.public_api_fast_api_impl import PublicFastAPI

dotenv.load_dotenv()
def main():
    db_client = DBClientRequestsImpl(os.environ.get("API_URL"))
    db = DBRequestsImpl(db_client=db_client)
    app = PublicFastAPI(db=db)
    uvicorn.run(app=app,
                host="0.0.0.0",
                port=int(os.environ.get("PUBLIC_API_PORT")))

if __name__ == "__main__":
    main()