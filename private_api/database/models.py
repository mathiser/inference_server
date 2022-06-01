from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, Boolean, PickleType, ForeignKey
from sqlalchemy.orm import declarative_base, relationship, object_session

Base = declarative_base()

class Model(Base):
    __tablename__ = "models"
    id = Column(Integer, primary_key=True)
    uid = Column(String, unique=True)
    human_readable_id = Column(String, unique=True, nullable=False)
    description = Column(String, nullable=True, default=None)
    container_tag = Column(String, nullable=False)
    use_gpu = Column(Boolean, default=True)
    model_available = Column(Boolean, default=False)
    model_zip = Column(String, nullable=True, unique=True, default=None)
    model_volume_uuid = Column(String, nullable=True, unique=True, default=None)
    model_mountpoint = Column(String, nullable=True, default=None)
    input_mountpoint = Column(String, nullable=False, default="/input")
    output_mountpoint = Column(String, nullable=False, default="/output")

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




class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True)
    uid = Column(String, unique=True)
    model_human_readable_id = Column(String, ForeignKey("models.human_readable_id"))
    datetime_created = Column(DateTime, default=datetime.utcnow)
    input_zip = Column(String, nullable=True, unique=True)
    output_zip = Column(String, nullable=True, unique=True)
    input_volume_uuid = Column(String, nullable=False, unique=True)
    output_volume_uuid = Column(String, nullable=False, unique=True)
    datetime_dispatched = Column(DateTime, nullable=True)
    datetime_finished = Column(DateTime, nullable=True)
    is_finished = Column(Boolean, default=False)

    def to_dict(self):
        return {
            "id": self.id,
            "uid": self.uid,
            "model_human_readable_id": self.model_human_readable_id,
            "datetime_created": self.datetime_created,
            "input_zip": self.input_zip,
            "input_volume_uuid": self.output_volume_uuid,
            "output_zip": self.output_zip,
            "output_volume_uuid": self.output_volume_uuid,
            "datetime_dispatched": self.datetime_dispatched,
            "datetime_finished": self.datetime_finished,
            "is_finished": self.is_finished
        }


