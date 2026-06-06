from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# Parse and normalize the connection URL
db_url = settings.DATABASE_URL
connect_args = {}

if db_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
elif db_url.startswith("postgres://"):
    # Normalize Render-provided postgres URLs
    db_url = db_url.replace("postgres://", "postgresql://", 1)
elif db_url.startswith("mysql://"):
    # Support TiDB Cloud or standard MySQL via pymysql
    db_url = db_url.replace("mysql://", "mysql+pymysql://", 1)

# Initialize engine
engine = create_engine(
    db_url, 
    connect_args=connect_args,
    pool_pre_ping=True  # Avoid database connection drops (ideal for TiDB Serverless/Render)
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
