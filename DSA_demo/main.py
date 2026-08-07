#set-up quick fastapi web app & configs

#figure out how to consume celery_app task to monitor and change user_script
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