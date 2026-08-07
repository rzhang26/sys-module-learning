
'''NOTE: settrace() is DEPRECATED, use 'sys.monitoring' instead...'''
import sys

def my_tracer(frame, event, arg):
    print(f'-> Event: {event} | Line: {frame.f_lineno} | Function: {frame.f_code.co_name}')

    if frame.f_locals:
        print(f'f_locals: {frame.f_locals}')

    return my_tracer

def calculate_sum(a, b):
    result = a + b
    return result

sys.settrace(my_tracer) #aka. start tracing 
calculate_sum(10, 20)
sys.settrace(None) #aka. stop tracing 