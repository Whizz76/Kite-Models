from datetime import datetime
def is_current_time_1515():
    # Get the current time
    current_time = datetime.now().time()
    print(current_time)
    print(current_time.hour)
    print(current_time.minute)
    # Check if the current time is 15:15 (3:15 PM)
    if current_time.hour == 0 and current_time.minute == 34:
        return True
    else:
        return False
    
print(is_current_time_1515())