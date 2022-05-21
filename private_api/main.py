import logging
import os

import dotenv
import uvicorn
from database.db_sql_impl import DB
from message_queue.rabbit_mq_impl import MQRabbitImpl
from fast_api import FastAPIImpl
from api import PrivateAPIImpl
LOG_FORMAT = '%(levelname)s:%(asctime)s:%(message)s'

logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
dotenv.load_dotenv()

def main():
    mq = MQRabbitImpl(host=os.environ.get("RABBIT_HOSTNAME"), port=int(os.environ.get("RABBIT_PORT")))
    api_backend = PrivateAPIImpl(db=DB, mq=mq)
    app = FastAPIImpl(api=api_backend)
    uvicorn.run(app=app, host="0.0.0.0", port=int(os.environ.get("API_PORT")))

if __name__ == "__main__":
    main()