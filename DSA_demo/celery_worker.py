from celery import Celery
import os

#Celery broker is on redis db index 0
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

celery_app = Celery(
    main='DSA_worker',
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=['DSA_demo.tasks']
)

# Explicitly register the task names so workers pick up tasks cleanly
# celery_app.autodiscover_tasks(["tasks"], force=True)

#configing celery app to have its tasks run in clean isolated processes
celery_app.conf.update(
    worker_concurrency=4,
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json'
)