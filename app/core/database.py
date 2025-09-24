from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.core.config import get_settings
from typing import Generator

settings = get_settings()

# Create database engine
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    echo=False  # Set to True for SQL query logging
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency to get database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """
    Create all database tables
    """
    from app.models.product import Base as ProductBase
    ProductBase.metadata.create_all(bind=engine)


def drop_tables():
    """
    Drop all database tables
    """
    from app.models.product import Base as ProductBase
    ProductBase.metadata.drop_all(bind=engine)


def reset_database():
    """
    Reset database by dropping and recreating all tables
    """
    drop_tables()
    create_tables()