from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# IMPORTANT: Replace 'YOUR_PASSWORD' with the password you set during installation.
DATABASE_URL = "postgresql://postgres:postgres@localhost/influence_os"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()