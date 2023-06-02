import secrets
from datetime import datetime
from typing import Union

from pydantic import BaseModel


class Model(BaseModel):
    human_readable_id: str
    description: Union[str, None]
    container_tag: str
    use_gpu: bool = True
    model_available: bool = True
    model_volume_id: Union[str, None]
    model_zip: Union[str, None]
    uid: str
    id: int


class Task(BaseModel):
    uid: str = secrets.token_urlsafe
    model_id: int
    model: Model
    datetime_created: datetime = datetime.now
    input_zip: Union[str, None] = None
    output_zip: Union[str, None] = None
    input_volume_id: str
    output_volume_id: str
    datetime_dispatched: Union[datetime, None] = None
    datetime_finished: Union[datetime, None] = None
    status: Union[int, None] = None
