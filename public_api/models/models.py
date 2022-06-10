from datetime import datetime

from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey


class Model(BaseModel):
    human_readable_id = Column(String, unique=True, nullable=False)
    description = Column(String, nullable=True)
    container_tag = Column(String, nullable=False)
    use_gpu = Column(Boolean, default=True)
    model_available = Column(Boolean, default=True)
    model_zip = Column(String, nullable=True)
    model_volume_uuid = Column(String, nullable=True)
    model_mountpoint = Column(String, nullable=True, default="/model")
    input_mountpoint = Column(String, nullable=False, default="/input")
    output_mountpoint = Column(String, nullable=False, default="/output")



class Task(BaseModel):
    id = Column(Integer, primary_key=True)
    uid = Column(String)
    model_human_readable_id = Column(String, ForeignKey("models.human_readable_id"))
    datetime_created = Column(DateTime, default=datetime.utcnow)
    input_zip = Column(String, nullable=False)
    output_zip = Column(String, nullable=False)
    input_volume_uuid = Column(String, nullable=False)
    output_volume_uuid = Column(String, nullable=False)
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
            "output_zip": self.output_zip,
            "input_volume_uuid": self.output_volume_uuid,
            "output_volume_uuid": self.output_volume_uuid,
            "datetime_dispatched": self.datetime_dispatched,
            "datetime_finished": self.datetime_finished,
            "is_finished": self.is_finished,
        }


