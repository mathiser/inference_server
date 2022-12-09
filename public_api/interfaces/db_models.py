from datetime import datetime
from typing import Union

from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey


# class Model(BaseModel):
#     human_readable_id = Column(String, unique=True, nullable=False)
#     description = Column(String, nullable=True)
#     container_tag = Column(String, nullable=False)
#     use_gpu = Column(Boolean, default=True)
#     model_available = Column(Boolean, default=True)
#     model_zip = Column(String, nullable=True)
#     model_volume_uuid = Column(String, nullable=True)
#     model_mountpoint = Column(String, nullable=True, default="/model")
#     input_mountpoint = Column(String, nullable=False, default="/input")
#     output_mountpoint = Column(String, nullable=False, default="/output")
#

class Model(BaseModel):
    human_readable_id: str
    description: Union[str, None]
    container_tag: str
    use_gpu: bool = True
    model_available: bool = True
    model_zip = str
    model_volume_uuid: Union[str, None]
    model_mountpoint: Union[str, None]
    input_mountpoint: Union[str, None]
    output_mountpoint: Union[str, None]


class Task(BaseModel):
    id: int
    uid: str
    model_human_readable_id: str
    datetime_created: datetime
    input_zip: str
    output_zip: str
    input_volume_uuid: str
    output_volume_uuid: str
    datetime_dispatched: Union[datetime, None]
    datetime_finished: Union[datetime, None]
    status: Union[int, None]
    #
    # def to_dict(self):
    #     return {
    #         "id": self.id,
    #         "uid": self.uid,
    #         "model_human_readable_id": self.model_human_readable_id,
    #         "datetime_created": self.datetime_created,
    #         "input_zip": self.input_zip,
    #         "output_zip": self.output_zip,
    #         "input_volume_uuid": self.output_volume_uuid,
    #         "output_volume_uuid": self.output_volume_uuid,
    #         "datetime_dispatched": self.datetime_dispatched,
    #         "datetime_finished": self.datetime_finished,
    #         "is_finished": self.is_finished,
    #     }
    #
    #
