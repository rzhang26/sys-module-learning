import sys

MY_TOOL_ID = sys.monitoring.DEBUGGER_ID

sys.monitoring.use_tool_id(MY_TOOL_ID, 'Events Use Case Demo')


def trace_start_callback(code, instruction_offset):
    print(f'[PY_START] Entering function: \'{code.co_name}\'')
    frame = sys._getframe(1)
    print(f'Arguments: {frame.f_locals}')
    return None 

def trace_return_callback(code, instruction_offset, retval):
    print(f'[PY_RETURN] Exciting function: \'{code.co_name}\'')
    print(f'Returning: {retval}')
    return None 

def trace_branch_left_callback(code, instruction_offset, target_offset):
    frame = sys._getframe(1)
    print(f'[BRANCH_LEFT (Not Taken)] Line {frame.f_lineno} in \'{code.co_name}\'')
    print(f'Bytecode offset stayed inline at {instruction_offset} (Target {target_offset} skipped)')
    return None

def trace_branch_right_callback(code, instruction_offset, target_offset):
    frame = sys._getframe(1)
    print(f'[BRANCH_Right (Taken)] Line {frame.f_lineno} in \'{code.co_name}\'')
    print(f'Bytecode offset jumped from {instruction_offset} -> to target {target_offset}')
    return None

sys.monitoring.register_callback(MY_TOOL_ID, sys.monitoring.events.PY_START, trace_start_callback)
sys.monitoring.register_callback(MY_TOOL_ID, sys.monitoring.events.PY_RETURN, trace_return_callback)
sys.monitoring.register_callback(MY_TOOL_ID, sys.monitoring.events.BRANCH_LEFT, trace_branch_left_callback)
sys.monitoring.register_callback(MY_TOOL_ID, sys.monitoring.events.BRANCH_RIGHT, trace_branch_right_callback)

tracked_events = (
    sys.monitoring.events.PY_START | 
    sys.monitoring.events.PY_RETURN | 
    sys.monitoring.events.BRANCH_LEFT | 
    sys.monitoring.events.BRANCH_RIGHT 
)

print('--- Monitoring Initiated ---')
sys.monitoring.set_events(MY_TOOL_ID, tracked_events)

sys.monitoring.set_events(MY_TOOL_ID, 0)
print("--- Monitoring Terminated ---")

