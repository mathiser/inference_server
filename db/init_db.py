import atexit
import os

import sqlalchemy
from sqlalchemy.orm import sessionmaker

from db.models import Base

data_dir = os.environ["DATA_DIR"]
input_base_folder = os.path.join(data_dir, "input")
output_base_folder = os.path.join(data_dir, "output")

for p in [input_base_folder, output_base_folder]:
    if not os.path.exists(p):
        os.makedirs(p)

DATABASE_URL = "sqlite:///", data_dir, "db.db"
engine = sqlalchemy.create_engine(DATABASE_URL, echo=True, future=True, connect_args={"check_same_thread": False})
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)


atexit.register(engine.dispose)
