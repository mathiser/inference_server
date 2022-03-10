import uuid
from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, Boolean, PickleType
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True)
    uid = Column(String)
    model_ids = Column(PickleType, default=[])
    datetime_created = Column(DateTime, default=datetime.utcnow)
    input_zip = Column(String, nullable=True)
    output_zip = Column(String, nullable=True)
    datetime_dispatched = Column(DateTime, nullable=True)
    datetime_finished = Column(DateTime, nullable=True)
    is_finished = Column(Boolean, default=False)

class Model(Base):
    __tablename__ = "models"
    id = Column(Integer, primary_key=True)
    human_readable_id = Column(String, unique=True, nullable=False)
    description = Column(String, nullable=True)
    container_tag = Column(String, nullable=False)
    use_gpu = Column(Boolean, default=True)
    model_available = Column(Boolean, default=True)
    model_zip = Column(String, nullable=True)
    model_volume = Column(String, nullable=True)
    model_mountpoint = Column(String, nullable=True)
    input_mountpoint = Column(String, nullable=False)
    output_mountpoint = Column(String, nullable=False)




