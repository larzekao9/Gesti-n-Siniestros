"""Celery application instance for background tasks."""

from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "siniestros",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    # El worker debe importar los módulos de tareas para registrarlas; sin esto
    # el worker arranca sin conocer las tasks y rechaza con "unregistered task".
    include=[
        "app.tasks.ai_analysis",
        "app.tasks.evidence_processing",
        "app.tasks.report_generation",
    ],
)

celery_app.conf.task_serializer = "json"
celery_app.conf.result_serializer = "json"
celery_app.conf.accept_content = ["json"]
celery_app.conf.timezone = "UTC"
celery_app.conf.enable_utc = True
