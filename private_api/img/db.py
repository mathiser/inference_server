import logging
import os
from time import sleep

import databases
import sqlalchemy
from sqlalchemy.orm import sessionmaker

from models import Base

LOG_FORMAT = '%(levelname)s:%(asctime)s:%(message)s'


logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)

# data volume mount point
data_dir = os.environ["DATA_DIR"]
input_base_folder = os.path.join(data_dir, "input")
output_base_folder = os.path.join(data_dir, "output")

# model volume mount point
model_base_folder = os.environ["MODELS_DIR"]

for p in [input_base_folder, output_base_folder, data_dir]:
    if not os.path.exists(p):
        os.makedirs(p)

DATABASE_URL = f'postgresql://{os.environ["DB_USER"]}:{os.environ["DB_PASSWORD"]}@{os.environ["DB_HOST"]}/{os.environ["DB_NAME"]}'

while True:
    try:
        engine = sqlalchemy.create_engine(DATABASE_URL, future=True)
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        database = databases.Database(DATABASE_URL)
        break
    except Exception as e:
        logging.error(e)
        sleep(1)
