import secrets
import uuid
from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True)
    uid = Column(String, default=secrets.token_urlsafe(32))
    container_tag = Column(String)
    model = Column(String, nullable=True)
    datetime_created = Column(DateTime, default=datetime.utcnow)

    input_zip = Column(String, nullable=True)
    output_zip = Column(String, nullable=True)


    datetime_dispatched = Column(DateTime, nullable=True)
    datetime_finished = Column(DateTime, nullable=True)
    is_finished = Column(Boolean, default=False)

