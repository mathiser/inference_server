import secrets
import uuid
from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Model(Base):
    __tablename__ = "models"

    id = Column(Integer, primary_key=True)
    uid = Column(String, default=secrets.token_urlsafe(32))

    description = Column(String, nullable=True)

    container_tag = Column(String)

    use_gpu = Column(Boolean, default=True)

    model_available = Column(Boolean, default=True)
    model_volume = Column(String, default=uid)

    tasks = relationship("Task", back_populates="model")
    input_mountpoint = Column(String, nullable=False)
    output_mountpoint = Column(String, nullable=False)
    model_mountpoint = Column(String, nullable=True)


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True)
    uid = Column(String, default=secrets.token_urlsafe(32))

    model_id = Column(Integer, ForeignKey("models.id"), nullable=False)
    model = relationship("Model", back_populates="tasks")

    datetime_created = Column(DateTime, default=datetime.utcnow)

    input_zip = Column(String, nullable=True)
    output_zip = Column(String, nullable=True)


    datetime_dispatched = Column(DateTime, nullable=True)
    datetime_finished = Column(DateTime, nullable=True)
    is_finished = Column(Boolean, default=False)
