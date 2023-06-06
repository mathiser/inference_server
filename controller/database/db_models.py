import os
import secrets
import tempfile
import uuid
from datetime import datetime

import sqlalchemy
from sqlalchemy import Integer, String, ForeignKey
from sqlalchemy.orm import sessionmaker, Mapped, mapped_column, relationship, DeclarativeBase


def generate_uuid():
    return str(uuid.uuid4())


class Base(DeclarativeBase):
    pass


class Model(Base):
    __tablename__ = "models"
    id: Mapped[int] = mapped_column(unique=True, primary_key=True, autoincrement=True)
    human_readable_id: Mapped[str] = mapped_column(unique=True, nullable=False)
    description: Mapped[str] = mapped_column(nullable=True, default=None)
    container_tag: Mapped[str]
    use_gpu: Mapped[bool] = mapped_column(default=True)
    model_available: Mapped[bool] = mapped_column(default=False)
    model_tar: Mapped[str] = mapped_column(nullable=True, unique=True, default=None)
    model_volume_id: Mapped[str] = mapped_column(unique=True, default=generate_uuid)

    def dict(self):
        return {
            "id": self.id,
            "human_readable_id": self.human_readable_id,
            "description": self.description,
            "container_tag": self.container_tag,
            "use_gpu": self.use_gpu,
            "model_available": self.model_available,
            "model_tar": self.model_tar,
            "model_volume_id": self.model_volume_id,
        }


class Task(Base):
    __tablename__ = "tasks"
    id: Mapped[str] = mapped_column(Integer, unique=True, primary_key=True, autoincrement=True)
    uid: Mapped[str] = mapped_column(String, unique=True, default=secrets.token_urlsafe, index=True)
    model_id: Mapped[str] = mapped_column(ForeignKey("models.id"))
    model: Mapped["Model"] = relationship(lazy="joined")
    datetime_created: Mapped[datetime] = mapped_column(default=datetime.now)
    input_tar: Mapped[str] = mapped_column(nullable=True, unique=True)
    output_tar: Mapped[str] = mapped_column(nullable=True, unique=True)
    datetime_dispatched: Mapped[datetime] = mapped_column(nullable=True)
    datetime_finished: Mapped[datetime] = mapped_column(nullable=True)
    status: Mapped[int] = mapped_column(nullable=False, default=-1)  # -1: pending, 0: failed, 1: finished, 2: running
    is_deleted: Mapped[bool] = mapped_column(nullable=False, default=False)

    def dict(self):
        return {
            "id": self.id,
            "uid": self.uid,
            "model_id": self.model_id,
            "model": self.model.dict(),
            "datetime_created": self.datetime_created,
            "input_tar": self.input_tar,
            "output_tar": self.output_tar,
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

    print(model.dict())

    human_readable_id = "some-model"
    container_tag = "hello-world"

    with tempfile.TemporaryDirectory() as tmp_dir:
        task = Task(model_id=model.id,
                    input_tar=os.path.abspath(os.path.join(tmp_dir, "uid", "input.tar.gz")),
                    output_tar=os.path.abspath(os.path.join(tmp_dir, "uid", "output.tar.gz")),
                    )
        with Session() as session:
            session.add(task)
            session.commit()
            session.refresh(task)

        print(task.dict())
