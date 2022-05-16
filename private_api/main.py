import logging
import os

import dotenv
import uvicorn
from database.db import DB
from message_queue.mq import MQ
from fast_api import FastAPIImpl
from api import PrivateAPIImpl
LOG_FORMAT = '%(levelname)s:%(asctime)s:%(message)s'

logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
dotenv.load_dotenv()
def main():
    mq = MQ(db=DB, host=os.environ.get("RABBIT_HOST"))
    api_backend = PrivateAPIImpl(db=DB, mq=mq)
    app = FastAPIImpl(api=api_backend)
    uvicorn.run(app=app, host="0.0.0.0", port=int(os.environ.get("API_PORT")))

if __name__ == "__main__":
    main()