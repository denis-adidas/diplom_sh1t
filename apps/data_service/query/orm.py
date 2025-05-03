import datetime

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from database import Base, engine, async_session_factory
from models import StudentsOrm, GroupOrm

class AsyncORM:

    @staticmethod
    async def create_tables():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)

    @staticmethod
    async def select_students():
        async with async_session_factory() as session:
            query = select(StudentsOrm)
            result = await session.execute(query)
            students = result.scalars().all()
            return students

    @staticmethod
    async def update_student(student_id: int, new_name: str):
        async with async_session_factory() as session:
            stmt = (
                update(StudentsOrm)
                .where(StudentsOrm.id == student_id)
                .values(
                    name=new_name,
                    updated_at=datetime.datetime.utcnow()
                )
            )
            await session.execute(stmt)
            await session.commit()

    @staticmethod
    async def insert_student(name: str, group_id: int):
        try:
            async with async_session_factory() as session:
                student = StudentsOrm(
                group_id=group_id,
                name=name
                )
                session.add(student)

                await session.commit()
        except IntegrityError as err:
            raise ValueError("need existing group for new student") from err

    @staticmethod
    async def select_group():
        async with async_session_factory() as session:
            query = select(GroupOrm)
            result = await session.execute(query)
            groups = result.scalars().all()
            return groups

    @staticmethod
    async def update_group(group_id: int, name: str):
        async with async_session_factory() as session:
            group = await session.get(GroupOrm, group_id)
            group.name = name
            await session.refresh(group)
            await session.commit()

    @staticmethod
    async def insert_group(name: str):
        async with async_session_factory() as session:
            group = GroupOrm(
                name=name
            )
            session.add(group)

            await session.commit()