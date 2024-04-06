# Ignore this file. It is just a test file.
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
    
def fun(el):
    if(el):
        return {"a":1}
    else: return None   

o=None
o=fun(False)
if(o!=None): print(o)
print(is_current_time_1515())

from datetime import datetime

# Get current date
current_date = datetime.now()

# Extract year's last two digits
year_last_two_digits = str(current_date.year)[-2:]

# Extract month index
month_index = str(current_date.month)
# Extract day
day = str(current_date.day)

if current_date.month<10:
    result_string = year_last_two_digits + month_index.zfill(1) + day.zfill(2)
# Form the string in the format yymdd
else: result_string = year_last_two_digits + month_index.zfill(2) + day.zfill(2)

sym="NIFTY"

trading_sym=sym+result_string
print(trading_sym)

def is_current_time(hour, minute):
    # Get current time
    current_time = datetime.now().time()
    
    # Check if current hour and minute match the parameters
    return current_time.hour == hour and current_time.minute == minute

print("time",is_current_time(15,15))
print("time",is_current_time(0, 24))

print(result_string)