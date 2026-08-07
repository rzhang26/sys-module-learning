import sys
import json
import redis

from DSA_demo.celery_app import app

#snapshots on redis db index = 1
r = redis.Redis(host='localhost', port=6379, db=1, decode_responses=True)

@app.task(name='tasks.execute_and_monitor_dsa')
def execute_and_monitor_dsa(session_id: str, user_code_string: str, target_function_name: str, input_arguments):
    r.delete(session_id)
    r.expire(session_id, 180)

    pre_allocated_vars = []
    MY_TOOL_ID = sys.monitoring.DEBUGGER_ID

    try:
        sys.monitoring.use_tool_id(MY_TOOL_ID, f'Worker_Engine_{session_id}')
    except ValueError:
        #Tool ID might already be registered in this specific worker process context
        pass

    def worker_start_callback(code, instruction_offset):
        nonlocal pre_allocated_vars
        if code.co_name == target_function_name:
            pre_allocated_vars = list(code.co_varnames)
            start_payload = {
                'event': 'START',
                'function': code.co_name,
                'expected_variables': pre_allocated_vars
            }

            r.rpush(session_id, json.dumps(start_payload))

        return None

    def worker_line_callback(code, line_number):
        if code.co_name == target_function_name:
            # Climb frame stack dynamically to step out of this monitoring callback
            frame = sys._getframe(1)

            while frame and frame.f_code.co_name != 'target_function_name': # frame.f_code.co_name is relative to each frame
                frame = frame.f_back
            if not frame:
                return None

            snapshot = {
                'event': 'STEP',
                'line': line_number,
                'function': code.co_name, #code.co_name is permanent
                'variables': {},
                'heap': {}
            }
            primitive_types = (int, str, bool, float) #tuple here

            for var_name, var_value in frame.f_locals.items():
                if isinstance(var_value, primitive_types) or var_value is None:
                    snapshot["variables"][var_name] = {"type": "primitive", "value": var_value}
                else:
                    mem_id = id(var_value)
                    snapshot["variables"][var_name] = {
                        "type": "reference", 
                        "target_address": mem_id
                    }
                    if isinstance(var_value, list):
                        snapshot["heap"][mem_id] = {
                            "type": "ARRAY", 
                            "elements": list(var_value)
                        }

            r.rpush(session_id, json.dumps(snapshot))
        return None

    sys.monitoring.register_callback(MY_TOOL_ID, sys.monitoring.events.PY_START, worker_start_callback)
    sys.monitoring.register_callback(MY_TOOL_ID, sys.monitoring.events.LINE, worker_line_callback)
    tracked_events = (
        sys.monitoring.events.PY_START | 
        sys.monitoring.events.LINE
        #could add more here
    )
    sys.monitoring.set_events(MY_TOOL_ID, tracked_events)

    #The INTERESTING portion
    try:
        sandbox_globals = {}
        compiled_user_code = compile(user_code_string, filename='<user_code>', mode='exec')
        exec(source=compiled_user_code, globals=sandbox_globals)

        target_function = sandbox_globals.get(target_function_name)
        if target_function: 
            target_function(input_arguments)
    except Exception as run_error:
        error_payload = {'event': 'CRASH', 'error': run_error}
        r.rpush(session_id, json.dumps(error_payload)) #json obj needs " not ' & is text string formatted
    finally:
        sys.monitoring.set_events(MY_TOOL_ID, 0)

    return {
        "status": "COMPLETE", 
        "session_id": session_id
    }

