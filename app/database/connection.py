from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import settings

Base = declarative_base()

engine = create_async_engine(
    settings.database_url,
    echo=settings.debug
)

AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def get_session() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session
