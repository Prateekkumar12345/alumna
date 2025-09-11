from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from chatbot_module.config import DATABASE_URI

# SQLAlchemy engine for PostgreSQL
engine = create_engine(
    DATABASE_URI,
    pool_size=20,
    max_overflow=0,
    pool_pre_ping=True,        # ✅ checks if connection is alive before using
    pool_recycle=1800          # ✅ recycle connections every 30 min (adjust as needed)
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for ORM models
Base = declarative_base()

# Dependency for getting DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
