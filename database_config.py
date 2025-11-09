#!/usr/bin/env python3
"""
Database configuration for Construction Estimation Project
"""

import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker

# Database connection settings
DATABASE_URL = "postgresql://postgres:parham81@localhost/construction_estimation"

# Create SQLAlchemy engine
engine = create_engine(DATABASE_URL)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class for models
Base = declarative_base()

def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def test_connection():
    """Test database connection using SQLAlchemy"""
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            print("✅ SQLAlchemy database connection successful!")
            return True
    except Exception as e:
        print(f"❌ SQLAlchemy connection error: {e}")
        return False

if __name__ == "__main__":
    test_connection() 