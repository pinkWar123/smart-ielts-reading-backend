#!/usr/bin/env python3
import os

from dotenv import load_dotenv
from sqlalchemy import create_engine

# Load environment variables
load_dotenv()

# Import models
from app.infrastructure.persistence.models import Base

# Get database URL
database_url = os.getenv("DATABASE_URL", "sqlite:///./ielts_platform.db")
print(f"🔗 Creating database: {database_url}")

# Create engine
engine = create_engine(database_url, echo=True)  # echo=True to see SQL commands

# Create all tables
print("\n📋 Creating tables...")
Base.metadata.create_all(bind=engine)

print(f"\n✅ Database created with tables: {list(Base.metadata.tables.keys())}")

# Check if database file exists (for SQLite)
if database_url.startswith("sqlite"):
    db_file = database_url.replace("sqlite:///", "")
    if os.path.exists(db_file):
        print(f"📁 Database file created: {db_file} ({os.path.getsize(db_file)} bytes)")
    else:
        print(f"❌ Database file not found: {db_file}")

print("\n🎉 Database setup completed!")
