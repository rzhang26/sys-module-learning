import sys
import json

from app.redis_client import r

RUN_ID = 'run:app_demo_session_001'

r.delete(RUN_ID)
r.expire(RUN_ID, 180)

MY_TOOL_ID = sys.monitoring.DEBUGGER_ID
sys.monitoring.use_tool_id(MY_TOOL_ID, 'app_demo')

def parse_and_store_snapshot(line_number):
    frame = sys._getframe(0)

    #skip our internal tracking callbacks (parse_and_store_snapshot & trace_line_callback)
    while frame and frame.f_code.co_name in ['parse_and_store_snapshot', 'trace_line_callback']:
        frame = frame.f_back

    if not frame:
        return 

    raw_locals = frame.f_locals #dict
    snapshot = {
        'line': line_number,
        'function': frame.f_code.co_name,
        'variables': {},
        'heap': {}
    }
    primitive_types = (int, str, bool, float)

    for var_name, var_val in raw_locals.items():
        if isinstance(var_val, primitive_types) or not var_val:
            snapshot['variables'][var_name] = {
                'type': 'primitive',
                'value': var_val
            }
        else:
            mem_address = id(var_val)
            snapshot['variables'][var_name] = {
                'type': 'reference',
                'target_address': mem_address
            }

            if isinstance(var_val, list):
                snapshot['heap'][mem_address] = {
                    'type': 'ARRAY',
                    'elements': list(var_val)
                }
            elif hasattr(var_val, '__dict__'): #elifcustom node object
                node_fields = {}
                for attr, val in var_val.__dict__.items():
                    if hasattr(val, '__dict__') or isinstance(val, list):
                        node_fields[attr] = {'type': 'pointer', 'target_address': id(val)}
                    else:
                        node_fields[attr] = {'type': 'value', 'value': val}

                snapshot['heap'][mem_address] = {
                    'type': 'OBJECT',
                    'className': var_val.__class__.__name__,
                    'fields': node_fields
                }

    r.rpush(RUN_ID, json.dumps(snapshot))
    #stores snapshot as a json obj into RUN_ID channel 

def trace_line_callback(code, line_number):
    #only traces the actual user function, skip external modules
    if code.co_name == 'reverse_array':
        parse_and_store_snapshot(line_number)
    return None

sys.monitoring.register_callback(MY_TOOL_ID, sys.monitoring.events.LINE, trace_line_callback)


#testing

#starts active tracing
sys.monitoring.set_events(MY_TOOL_ID, sys.monitoring.events.LINE)

def reverse_array(arr):
    left = 0
    right = len(arr) - 1
    while left < right:
        arr[left], arr[right] = arr[right], arr[left]
        left += 1
        right -= 1
    return arr

print("--- Executing User Code and Saving to Redis ---")
test_data = [10, 20, 30, 40]
reverse_array(test_data)

#stops 
sys.monitoring.set_events(MY_TOOL_ID, 0)

print("\n--- Verifying Stored Data From Redis List ---")
all_steps = r.lrange(RUN_ID, 0, -1)
print(f"Total step snapshots captured: {len(all_steps)}")

# Print out the very first execution step snapshot to see its structure
if all_steps:
    first_step = json.loads(all_steps[1])
    print("\nExample of Step 1 Snapshot JSON in Redis:")
    print(json.dumps(first_step, indent=2))