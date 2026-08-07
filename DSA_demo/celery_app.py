from celery import Celery
import os

#Celery broker is on redis db index 0
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

app = Celery(
    main='DSA_tasks',
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=['tasks']
)

#configing celery app to have its tasks run in clean isolated processes
app.conf.update(
    worker_concurrency=4,
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json'
)