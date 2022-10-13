from threading import Thread
from pubsub import pub

class Scheduler(Thread):
    def __init__(self, appData):
        Thread.__init__(self)
        self.appData = appData

        pub.subscribe(self.OnTimer, 'ping-timer')
        self.start()

    def run(self):
        ...

    def OnTimer(self):
        self.sec += 1


users = ['m', 'g', 'h', 's']
line = []
len = 4

def recur(index, n_insertions):
    if len(line) == 0:
        line.insert(index, users[index])

    else:
        len
    
    recur(index + 1, n_insertions + 1)


def binary_search(arr, low, high, x):
 
    # Check base case
    if high >= low:
 
        mid = (high + low) // 2
 
        # If element is present at the middle itself
        if arr[mid] == x:
            return mid
 
        # If element is smaller than mid, then it can only
        # be present in left subarray
        elif arr[mid] > x:
            return binary_search(arr, low, mid - 1, x)
 
        # Else the element can only be present in right subarray
        else:
            return binary_search(arr, mid + 1, high, x)
 
    else:
        # Element is not present in the array
        return -1
 
# Test array
arr = [ 2, 3, 4, 10, 40 ]
x = 10
 
# Function call
result = binary_search(arr, 0, len(arr)-1, x)
 
if result != -1:
    print("Element is present at index", str(result))
else:
    print("Element is not present in array")