import datetime

from typing import Annotated, Optional
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import text, ForeignKey
from database import Base
from pydantic import BaseModel

intpk = Annotated[int, mapped_column(primary_key=True)]
created_at = Annotated[datetime.datetime, mapped_column(server_default=text("TIMEZONE('utc', now())"))]
updated_at = Annotated[datetime.datetime, mapped_column(
        server_default=text("TIMEZONE('utc', now())"),
        onupdate=datetime.datetime.now(datetime.UTC),
    )]


# ORM

class StudentsOrm(Base):
    __tablename__ = "students"

    id: Mapped[intpk]
    name: Mapped[str]
    group_id: Mapped[int] = mapped_column(ForeignKey("group.id"))
    group: Mapped[ "GroupOrm"] = relationship(back_populates="students")
    created_at: Mapped[created_at]
    updated_at: Mapped[updated_at]


class GroupOrm(Base):
    __tablename__ = "group"

    id: Mapped[intpk]
    name: Mapped[str]
    students: Mapped[list["StudentsOrm"]] = relationship(back_populates="group")

# API MODELS

#students
class PostNewStudentBody(BaseModel):
    name: str
    group_id: int

class PostUpdateStudentBody(BaseModel):
    student_id: int
    new_name: str

# groups
class PostNewGroupBody(BaseModel):
    name: str

class PostUpdateGroupBody(BaseModel):
    group_id: int
    name: str