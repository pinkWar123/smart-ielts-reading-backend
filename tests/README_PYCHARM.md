# Running Tests in PyCharm

## Quick Start

### 1. Run All Tests in a Class
Open any test file (e.g., `test_session_use_cases.py`) and you'll see green ▶ arrows:
- **Next to class name** → Click to run all tests in that class
- **Next to each test function** → Click to run that specific test
- **At the file top** → Click to run all tests in the file

### 2. Run Tests with Keyboard Shortcuts
- **Ctrl+Shift+R** (Mac) / **Ctrl+Shift+F10** (Win/Linux) → Run test at cursor
- **Ctrl+R** (Mac) / **Shift+F10** (Win/Linux) → Re-run last test

## Test Organization

### Unit Tests (Organized by Class)
```
tests/unit/use_cases/sessions/
├── test_session_use_cases.py          ← All tests organized by class (recommended)
├── test_create_session_use_case.py    ← Individual test files
├── test_list_sessions_use_case.py
├── test_get_session_by_id_use_case.py
└── test_get_my_sessions_use_case.py
```

**Best Practice**: Use `test_session_use_cases.py` - it groups all related tests into classes, so you can:
- Run all CreateSession tests by clicking the `TestCreateSessionUseCase` class arrow
- Run all ListSessions tests by clicking the `TestListSessionsUseCase` class arrow
- Run ALL session tests by clicking the file-level arrow

### Example Test Class Structure
```python
class TestCreateSessionUseCase:
    """Click the arrow next to this line to run ALL create session tests"""

    @pytest.mark.asyncio
    async def test_create_session_success(self, ...):
        # Test implementation

    @pytest.mark.asyncio
    async def test_create_session_fails_permission(self, ...):
        # Test implementation
```

## PyCharm Configuration

### Already Configured ✅
- ✅ pytest as default test runner
- ✅ `pytest.ini` with async support
- ✅ `tests/` marked as test sources root
- ✅ Test discovery patterns configured

### If Tests Don't Show Run Buttons

**Step 1**: Mark tests directory as Test Sources Root
- Right-click `tests/` folder → **Mark Directory as** → **Test Sources Root**

**Step 2**: Configure pytest as default runner
- **PyCharm → Settings → Tools → Python Integrated Tools**
- Set **Default test runner** to `pytest`

**Step 3**: Invalidate caches (if needed)
- **File → Invalidate Caches → Invalidate and Restart**

## Running Tests from Command Line

```bash
# Run all unit tests
python -m pytest tests/unit/ -v

# Run all session tests
python -m pytest tests/unit/use_cases/sessions/ -v

# Run specific test class
python -m pytest tests/unit/use_cases/sessions/test_session_use_cases.py::TestCreateSessionUseCase -v

# Run specific test
python -m pytest tests/unit/use_cases/sessions/test_session_use_cases.py::TestCreateSessionUseCase::test_create_session_success -v

# Run with coverage
python -m pytest tests/unit/ --cov=app/application/use_cases/sessions
```

## Test Results Summary

### ✅ All Unit Tests Pass (21/21)
- **CreateSessionUseCase**: 8 tests
- **ListSessionsUseCase**: 5 tests
- **GetSessionByIdUseCase**: 4 tests
- **GetMySessionsUseCase**: 4 tests

## Tips

1. **Run tests frequently** - Use keyboard shortcuts for quick iterations
2. **Use test classes** - Organize related tests together for batch running
3. **Watch mode** - Right-click test → "Run with Coverage" for detailed analysis
4. **Debug tests** - Click the debug icon 🐛 instead of ▶ to debug with breakpoints

## Integration Tests

Integration tests are in `tests/integration/` but require:
- Full app setup with database
- Proper fixtures for authentication
- More time to run

For quick feedback during development, **focus on unit tests**.