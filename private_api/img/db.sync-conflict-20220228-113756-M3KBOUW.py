import logging
import os
from time import sleep

import databases
import sqlalchemy
from sqlalchemy.orm import sessionmaker

from models import Base

LOG_FORMAT = '%(levelname)s:%(asctime)s:%(message)s'
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)

"""
Script to initiate DB
"""

# data volume mount point
data_dir = os.environ["DATA_DIR"] # Base dir for inputs and outputs
input_base_folder = os.path.join(data_dir, "input") # Dir for inputs
output_base_folder = os.path.join(data_dir, "output") # Dir for outputs

# model volume mount point
model_base_folder = os.environ["MODELS_DIR"]

# If not db-locations exists, they are made.
for p in [input_base_folder, output_base_folder, data_dir]:
    if not os.path.exists(p):
        os.makedirs(p)

# db_containers URL
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
        sleep(5)
