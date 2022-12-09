import os
import secrets
import tempfile
from datetime import datetime

import sqlalchemy
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()


class Model(Base):
    __tablename__ = "models"
    id = Column(Integer, unique=True, primary_key=True, autoincrement=True)
    uid = Column(String, unique=True, default=secrets.token_hex, index=True)
    human_readable_id = Column(String, unique=True, nullable=False)
    description = Column(String, nullable=True, default=None)
    container_tag = Column(String, nullable=False)
    use_gpu = Column(Boolean, default=True)
    model_available = Column(Boolean, default=False)
    model_zip = Column(String, nullable=True, unique=True, default=None)
    model_volume_id = Column(String, unique=True, default=secrets.token_hex)

    def to_dict(self):
        return {
            "id": self.id,
            "human_readable_id": self.human_readable_id,
            "description": self.description,
            "container_tag": self.container_tag,
            "use_gpu": self.use_gpu,
            "model_available": self.model_available,
            "model_zip": self.model_zip,
            "model_volume_id": self.model_volume_id,
        }

class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, unique=True, primary_key=True, autoincrement=True)
    uid = Column(String, unique=True, default=secrets.token_hex, index=True)
    model_human_readable_id = Column(String, ForeignKey("models.human_readable_id"))
    datetime_created = Column(DateTime, default=datetime.now)
    input_zip = Column(String, nullable=True, unique=True)
    output_zip = Column(String, nullable=True, unique=True)
    input_volume_id = Column(String, nullable=False, unique=True, default=secrets.token_hex)
    output_volume_id = Column(String, nullable=False, unique=True, default=secrets.token_hex)
    datetime_dispatched = Column(DateTime, nullable=True)
    datetime_finished = Column(DateTime, nullable=True)
    status = Column(Integer, nullable=False, default=-1)  # -1: pending, 0: failed, 1: finished, 2: running
    is_deleted = Column(Boolean, nullable=False, default=False)

    def to_dict(self):
        return {
            "id": self.id,
            "model_human_readable_id": self.model_human_readable_id,
            "datetime_created": self.datetime_created,
            "input_zip": self.input_zip,
            "output_zip": self.output_zip,
            "input_volume_id": self.output_volume_id,
            "output_volume_id": self.output_volume_id,
            "datetime_dispatched": self.datetime_dispatched,
            "datetime_finished": self.datetime_finished,
            "status": self.status,
            "is_deleted": self.is_deleted
        }


if __name__ == "__main__":
    database_url = f'sqlite://'

    engine = sqlalchemy.create_engine(database_url, future=True)
    Base.metadata.create_all(engine)

    Session = sessionmaker(bind=engine)
    
    human_readable_id = "some-model"
    description = "Some-niiiice-model"
    container_tag = "hello-world"
    use_gpu = False

    model = Model(human_readable_id=human_readable_id,
                  description=description,
                  container_tag=container_tag,
                  use_gpu=use_gpu)
    with Session() as session:
        session.add(model)
        session.commit()
        session.refresh(model)

    print(model.to_dict())

    human_readable_id = "some-model"
    container_tag = "hello-world"

    with tempfile.TemporaryDirectory() as tmp_dir:

        task = Task(model_human_readable_id=human_readable_id,
                    input_zip=os.path.abspath(os.path.join(tmp_dir, "uid", "input.zip")),
                    output_zip=os.path.abspath(os.path.join(tmp_dir, "uid", "output.zip")),
                    )
        with Session() as session:
            session.add(task)
            session.commit()
            session.refresh(task)

        print(task.to_dict())