Generic single-database configuration.

## Alembic Migration Commands

### Create Migrations

Create a new migration (auto-generate from model changes):
```bash
alembic revision --autogenerate -m "description of changes"
```

Create an empty migration (manual):
```bash
alembic revision -m "description"
```

### Apply Migrations

Apply all pending migrations:
```bash
alembic upgrade head
```

Upgrade to a specific version:
```bash
alembic upgrade <revision_id>
```

### Rollback Migrations

Downgrade one version:
```bash
alembic downgrade -1
```

Downgrade to a specific version:
```bash
alembic downgrade <revision_id>
```

Downgrade all migrations:
```bash
alembic downgrade base
```

### View Migration Status

Check current migration version:
```bash
alembic current
```

View migration history:
```bash
alembic history
```

View migration history with details:
```bash
alembic history --verbose
```

## Notes

- Make sure your `.env` file has the correct database connection string before running migrations
- The database URL is configured via environment variable (overridden in env.py)
- Migrations are located in `migrations/versions/`