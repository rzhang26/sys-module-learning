#set-up quick fastapi web app & configs

#figure out how to consume celery_app task to monitor and change user_script via endpoint
#routing database operations through Celery workers (celery_app instance)
#user_script example:
user_script = '''
class Node:
    def __init__(self, data=None):
        self.data = data  # Stores the value
        self.next = None  # Points to the next node

# Create individual nodes
node1 = Node(10)
node2 = Node(20)

# Link them together
node1.next = node2

print(node1.data)       # Outputs: 10
print(node1.next.data)  # Outputs: 20
'''

import json
import uvicorn
import uuid
import redis
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field

from DSA_demo.celery_worker import celery_app

#connects FastAPI router to our snapshot warehouse database index (DB 1)
redis_client = redis.Redis(host='localhost', port=6379, db=1, decode_responses=True)

app = FastAPI(title='DSA_demo', description="FastAPI + Celery + sys.monitoring test pipeline")

#enables input fields to show up in swagger UI
class RunCodeRequest(BaseModel):
    user_code: str = Field(
        ..., 
        description='Raw string python code to run.', 
        examples=['def reverse_array(arr):\n    left = 0\n    right = len(arr) - 1\n    while left < right:\n        arr[left], arr[right] = arr[right], arr[left]\n        left += 1\n        right -= 1']
    )
    target_function: str = Field(..., description='The explicit name of the function to monitor.', example="reverse_array")
    input_arguments: list = Field(..., description='The testing array argument data structure package.', example=[10, 20, 30, 40])

@app.post('/api/run', summary='Trigger Background Code Monitoring Tracing Task')
def trigger_code_execution(payload: RunCodeRequest):
    session_id = f'run:{uuid.uuid4()}'

    celery_app.send_task(
        name='tasks.execute_and_monitor_dsa', 
        args=[session_id, payload.user_code, payload.target_function, payload.input_arguments])

    return {
        'status': 'PROCESSING',
        'session_id': session_id,
        'message': 'Task forwarded to Celery worker queue. Poll the get_execution_snapshots endpoint below using this session_id'
    }

@app.get('/api/results/{session_id}', summary='Fetch Captured State Memory Snapshots Matrix')
def get_execution_snapshots(session_id: str):
    raw_history = redis_client.lrange(session_id, 0, -1)

    if not raw_history:
        if redis_client.exists(session_id):
            return {
                'status': 'RUNNING',
                'snapshots': []
            }
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Execution session key not found or expired')

    parsed_snapshots = [json.loads(snapshot) for snapshot in raw_history]

    return {
        'status': 'COMPLETE' if parsed_snapshots[-1].get('event') in ['STEP', 'CRASH'] else 'PROCESSING',
        'total_steps': len(parsed_snapshots),
        'snapshots': parsed_snapshots
    }