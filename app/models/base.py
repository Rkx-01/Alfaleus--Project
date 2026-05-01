from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.ext.declarative import as_declarative, declared_attr
from app.utils.config import settings

# Create Async Engine
engine = create_async_engine(settings.DATABASE_URL, echo=False)

# Create Async Session factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

@as_declarative()
class Base:
    id: any
    __name__: str
    
    @declared_attr
    def __tablename__(cls) -> str:
        return cls.__name__.lower()

async def get_db():
    """Dependency for providing async database sessions."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
