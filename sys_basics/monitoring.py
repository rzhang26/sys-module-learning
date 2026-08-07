import sys

MY_TOOL_ID = sys.monitoring.DEBUGGER_ID

sys.monitoring.use_tool_id(MY_TOOL_ID, 'Example_application')

#define callback function
def trace_line_callback(code, line_number):
    print(f'\nCallback at line {line_number} in function \'{code.co_name}\'')
    
    frame = sys._getframe(1) 
    
    current_variables = frame.f_locals
    if current_variables:
        print(f'Current Variables: {current_variables}')

    # Returning None keeps the sticky note active.
    # Returning sys.monitoring.DISABLE permanently removes the sticky note for this line.
    return None

#binding callback to event
sys.monitoring.register_callback(
    MY_TOOL_ID, 
    sys.monitoring.events.LINE,
    trace_line_callback
)

#start monitoring (tracing but better)
sys.monitoring.set_events(MY_TOOL_ID, sys.monitoring.events.LINE)

def reverse_array(arr):
    left = 0
    right = len(arr) - 1
    while left < right:
        arr[left], arr[right] = arr[right], arr[left]
        left += 1
        right -= 1
    return arr

print('--- Starting Execution Loop ---')
test_data = [10, 20, 30]
reverse_array(test_data)

#stop monitoring
sys.monitoring.set_events(MY_TOOL_ID, 0)
print('\n--- Monitoring Disabled ---')