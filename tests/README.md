# Tests

## Running Tests

To run the DI system tests:

```bash
# Install pytest if not already installed
pip install pytest pytest-asyncio

# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_di_system.py -v

# Run with coverage
pytest tests/ --cov=app
```

## Test Structure

- `test_di_system.py` - Tests for dependency injection system, verifying:
  - Controllers get proper dependencies with sessions
  - Repositories receive correct sessions
  - Session isolation between requests
  - Multiple repositories share the same session within a request