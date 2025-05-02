import asyncio

from config import settings
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

engine = create_async_engine(
    url = settings.DATABASE_URL_async,
    echo=True,
    pool_size=5,
    max_overflow=10,
)

async_session_factory = async_sessionmaker(engine)

class Base(DeclarativeBase):
    pass