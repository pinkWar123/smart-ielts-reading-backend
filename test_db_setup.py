#!/usr/bin/env python3

import os
import sys

from dotenv import load_dotenv
from sqlalchemy import create_engine

# Add the current directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Load environment variables
load_dotenv()

# Import models
try:
    from app.infrastructure.persistence.models import Base

    print("✅ Models imported successfully")
except Exception as e:
    print(f"❌ Error importing models: {e}")
    sys.exit(1)

# Test database connection
try:
    database_url = os.getenv("DATABASE_URL", "sqlite:///./ielts_platform.db")
    print(f"🔗 Connecting to database: {database_url}")

    engine = create_engine(database_url)

    # Test connection
    with engine.connect() as conn:
        print("✅ Database connection successful")

    # Create all tables
    Base.metadata.create_all(bind=engine)
    print("✅ Tables created successfully")

    # List all tables
    print(f"📋 Tables created: {list(Base.metadata.tables.keys())}")

except Exception as e:
    print(f"❌ Database error: {e}")
    sys.exit(1)

print("🎉 Database setup completed successfully!")
