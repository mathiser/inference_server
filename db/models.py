from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True)
    uid = Column(String)

    input_zip = Column(String)
    output_zip = Column(String, nullable=True)
    container_tag = Column(String)

    datetime_created = Column(DateTime, default=datetime.utcnow)
    datetime_dispatched = Column(DateTime, nullable=True)
    datetime_finished = Column(DateTime, nullable=True)
    is_finished = Column(Boolean, default=False)

