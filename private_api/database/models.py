from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, Boolean, PickleType
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True)
    uid = Column(String)
    model_ids = Column(PickleType, default=[])
    human_readable_ids = Column(PickleType, default=[])
    datetime_created = Column(DateTime, default=datetime.utcnow)
    input_zip = Column(String, nullable=True)
    output_zip = Column(String, nullable=True)
    input_volume_uuid = Column(String, nullable=False)
    output_volume_uuid = Column(String, nullable=False)
    datetime_dispatched = Column(DateTime, nullable=True)
    datetime_finished = Column(DateTime, nullable=True)
    is_finished = Column(Boolean, default=False)

    def to_dict(self):
        return {
            "id": self.id,
            "uid": self.uid,
            "model_ids": self.model_ids,
            "human_readable_ids": self.human_readable_ids,
            "datetime_created": self.datetime_created,
            "input_zip": self.input_zip,
            "input_volume_uuid": self.output_volume_uuid,
            "output_zip": self.output_zip,
            "output_volume_uuid": self.output_volume_uuid,
            "datetime_dispatched": self.datetime_dispatched,
            "datetime_finished": self.datetime_finished,
            "is_finished": self.is_finished
        }

class Model(Base):
    __tablename__ = "models"
    id = Column(Integer, primary_key=True)
    uid = Column(String)
    human_readable_id = Column(String, unique=True, nullable=False)
    description = Column(String, nullable=True)
    container_tag = Column(String, nullable=False)
    use_gpu = Column(Boolean, default=True)
    model_available = Column(Boolean, default=True)
    model_zip = Column(String, nullable=True)
    model_volume_uuid = Column(String, nullable=True)
    model_mountpoint = Column(String, nullable=True)
    input_mountpoint = Column(String, nullable=False)
    output_mountpoint = Column(String, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "uid": self.uid,
            "human_readable_id": self.human_readable_id,
            "description": self.description,
            "container_tag": self.container_tag,
            "use_gpu": self.use_gpu,
            "model_available": self.model_available,
            "model_zip": self.model_zip,
            "model_volume_uuid": self.model_volume_uuid,
            "model_mountpoint": self.model_mountpoint,
            "input_mountpoint": self.input_mountpoint,
            "output_mountpoint": self.output_mountpoint,
        }





