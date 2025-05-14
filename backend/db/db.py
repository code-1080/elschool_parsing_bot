from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase


engine = create_async_engine('sqlite+aiosqlite:///database.db', echo=True)

async_session = async_sessionmaker(
    engine,
    expire_on_commit=False,
    class_=AsyncSession
)


class Base(DeclarativeBase):
    pass


async def setup_db():
    async with engine.begin() as conn:
        from backend.db.models.user import UserModel
        await conn.run_sync(Base.metadata.create_all)


async def get_session():
    async with async_session() as session:
        return session
