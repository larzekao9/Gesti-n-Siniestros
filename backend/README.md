# Backend - Gestión de Siniestros

FastAPI + PostgreSQL + Redis backend.

This directory is managed by the backend-django agent.
The Dockerfile is ready and will build once the application code is in place.

## Expected structure

```
backend/
  app/
    main.py          # FastAPI entrypoint
    core/
      celery_app.py  # Celery configuration
    ...
  tests/
  scripts/
    seed.py
  requirements.txt
  alembic.ini
```
