from datetime import datetime
from typing import Union

from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey

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