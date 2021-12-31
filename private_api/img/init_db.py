import logging
import os
from time import sleep

import databases
import sqlalchemy
from sqlalchemy.orm import sessionmaker

from models import Base

data_dir = os.environ["DATA_DIR"]
input_base_folder = os.path.join(data_dir, "input")
output_base_folder = os.path.join(data_dir, "output")

for p in [input_base_folder, output_base_folder, data_dir]:
    if not os.path.exists(p):
        os.makedirs(p)

DATABASE_URL = f'postgresql://{os.environ["DB_USER"]}:{os.environ["DB_PASSWORD"]}@{os.environ["DB_HOST"]}/{os.environ["DB_NAME"]}'

while True:
    try:
        engine = sqlalchemy.create_engine(DATABASE_URL, future=True)
        break
    except Exception as e:
        logging.error(e)
        sleep(1)

Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

database = databases.Database(DATABASE_URL)
