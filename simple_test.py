#!/usr/bin/env python3
import sys

print("Python version:", sys.version)
print("Python executable:", sys.executable)

try:
    print("Step 1: Importing base...")
    from app.infrastructure.persistence.models.base import Base

    print("✅ Base imported successfully")
    print("Tables in Base metadata:", list(Base.metadata.tables.keys()))
except Exception as e:
    print("❌ Error importing base:", e)
    import traceback

    traceback.print_exc()
    sys.exit(1)

try:
    print("\nStep 2: Importing all models...")
    from app.infrastructure.persistence.models import (
        AttemptModel,
        PassageModel,
        QuestionModel,
        TestModel,
        UserModel,
    )

    print("✅ All models imported successfully")
    print("Final tables:", list(Base.metadata.tables.keys()))
except Exception as e:
    print("❌ Error importing models:", e)
    import traceback

    traceback.print_exc()
    sys.exit(1)

print("\n🎉 All imports successful!")
