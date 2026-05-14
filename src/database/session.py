from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from src.config import config

# Создание движка БД (используем asyncpg для асинхронных операций)
# DATABASE_URL в .env должен быть postgresql+asyncpg://...
database_url = str(config.DATABASE_URL).replace("postgresql+psycopg2", "postgresql+asyncpg")
engine = create_async_engine(database_url, echo=False)

# Создание фабрики сессий
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_session() -> AsyncSession:
    """
    Генератор для получения сессии БД
    
    Используется как dependency в FastAPI или для ручного управления
    """
    async with AsyncSessionLocal() as session:
        yield session
