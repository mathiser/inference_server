import secrets
from datetime import datetime
from typing import Union

from pydantic import BaseModel


class Model(BaseModel):
    id: int
    human_readable_id: str
    description: Union[str, None]
    container_tag: str
    use_gpu: bool = True
    model_available: bool = True
    model_volume_id: Union[str, None]
    model_tar: Union[str, None]
    pull_on_every_run: bool = True
    dump_logs: bool = True


class Task(BaseModel):
    id: int
    uid: str
    model_id: int
    model: Model
    datetime_created: datetime = datetime.now
    input_tar: Union[str, None] = None
    output_tar: Union[str, None] = None
    datetime_dispatched: Union[datetime, None] = None
    datetime_finished: Union[datetime, None] = None
    status: Union[int, None] = None
    is_deleted: Union[bool, None] = None
