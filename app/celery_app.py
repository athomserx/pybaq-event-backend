from celery import Celery

from app.config import settings

celery_app = Celery(
    "tasks.*",
    broker=settings.celery_broker_url,
    backend=settings.celery_broker_url,
    broker_connection_retry_on_startup=True,
)

celery_app.autodiscover_tasks(["app.tasks"])
