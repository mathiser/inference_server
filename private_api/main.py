import logging
import os

import dotenv
import uvicorn

from database.db_sql_impl import DBSQLiteImpl
from api import APIFastAPIImpl
from message_queue.rabbit_mq_impl import MQRabbitImpl

LOG_FORMAT = '%(levelname)s:%(asctime)s:%(message)s'

logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
dotenv.load_dotenv()

def main():
    mq = MQRabbitImpl(host=os.environ.get("RABBIT_HOSTNAME"),
                      port=int(os.environ.get("RABBIT_PORT")),
                      unfinished_queue_name=os.environ.get("UNFINISHED_JOB_QUEUE"),
                      finished_queue_name=os.environ.get("FINISHED_JOB_QUEUE"))

    db = DBSQLiteImpl(base_dir=os.environ["DATA_DIR"])
    app = APIFastAPIImpl(db=db, mq=mq)
    uvicorn.run(app=app, host="0.0.0.0", port=int(os.environ.get("API_PORT")))

if __name__ == "__main__":
    main()