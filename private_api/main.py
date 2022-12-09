import logging
import os

import dotenv
import uvicorn
dotenv.load_dotenv()

from database.db_sql_impl import DBSQLiteImpl
from api import APIFastAPIImpl
from message_queue.rabbit_mq_impl import MQRabbitImpl

LOG_FORMAT = '%(levelname)s:%(asctime)s:%(message)s'

logging.basicConfig(level=int(os.environ.get("LOG_LEVEL")), format=LOG_FORMAT)

def main():
    mq = MQRabbitImpl(host=os.environ.get("RABBIT_HOSTNAME"),
                      port=int(os.environ.get("RABBIT_PORT")),
                      unfinished_queue_name=os.environ.get("UNFINISHED_JOB_QUEUE"),
                      finished_queue_name=os.environ.get("FINISHED_JOB_QUEUE"))

    db = DBSQLiteImpl(base_dir=os.environ.get("DATA_DIR")) # HARDCODED as it is easier to maintain
    app = APIFastAPIImpl(db=db, mq=mq)
    uvicorn.run(app=app, host="0.0.0.0", port=int(os.environ.get("API_PORT")))

if __name__ == "__main__":
    main()