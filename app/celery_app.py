from celery import Celery

from app.config import settings

celery_app = Celery(
    "app",
    broker=settings.celery_broker_url,
    backend=settings.celery_broker_url,
)

celery_app.autodiscover_tasks(["app.tasks"])
