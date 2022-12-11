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


class Task(BaseModel):
    uid: str
    model_human_readable_id: str
    datetime_created: datetime
    input_zip: str
    output_zip: str
    input_volume_id: str
    output_volume_id: str
    datetime_dispatched: Union[datetime, None]
    datetime_finished: Union[datetime, None]
    status: Union[int, None]