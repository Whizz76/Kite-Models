import pandas as pd
from datetime import datetime

strike_price=40700
expiry_day="02-03-2023"
date="02-03-2023"
# reversed_day=''.join(reversed(day))

input_date=expiry_day.split("-")
input_date_string=''.join(reversed(input_date))
reversed_day='-'.join(reversed(date.split("-")))

# Reading the call and put data

call_data=pd.read_csv("./Data_BNF/Data_BNF/"+expiry_day+"/BNF"+input_date_string+str(strike_price)+"CE.csv")
put_data=pd.read_csv("./Data_BNF/Data_BNF/"+expiry_day+"/BNF"+input_date_string+str(strike_price)+"PE.csv")

# Getting the call and put data during the start i.e here from 10 AM

open_c=call_data[call_data["datetime"].str.contains(reversed_day+" 10")].iloc[0]
open_p=put_data[put_data["datetime"].str.contains(reversed_day+" 10")].iloc[0]

# Getting the start time for both call and put

open_c_time=open_c["datetime"]
open_p_time=open_p["datetime"]

# If the start time of call and put are different, adjust them to be equal to each other

if(open_c_time>open_p_time):
    open_p=put_data[put_data["datetime"].str.contains(open_c_time)].iloc[0]
elif(open_p_time>open_c_time):
    open_c=call_data[call_data["datetime"].str.contains(open_p_time)].iloc[0]

# Getting the price during the start for both call and put 
call_start=open_c["close"]
put_start=open_p["close"]

# Setting the stoploss as 30%

stoploss=0.3

# Setting the closing prices for both call and put

call_stop=call_start*(1+stoploss)
put_stop=put_start*(1+stoploss)

# Getting the call and put data on that particular day after 10 AM

call_data_1=call_data[call_data["datetime"].str.contains(reversed_day+" 1")]
put_data_1=put_data[put_data["datetime"].str.contains(reversed_day+" 1")]

call_data_1=call_data_1.reset_index(drop=True)
put_data_1=put_data_1.reset_index(drop=True)

# Setting the stop time for call and put

call_stop_time=None
put_stop_time=None

print("call_start {},call_stop {},put_start {},put_stop {}".format(call_start,call_stop,put_start,put_stop))

# Iterating through the call data till 15:20 unless we reach the limit

for i in range(len(call_data_1)):
    call_time=call_data_1.loc[i,"datetime"].split(" ")[1][0:5].strip()
    if(call_data_1.loc[i,"close"]>=call_stop):
        call_stop=call_data_1.loc[i,"close"]
        call_stop_time=call_data_1.loc[i,"datetime"]
        break
    elif(call_time=="15:20"):
        call_stop=call_data_1.loc[i,"close"]
        call_stop_time=call_data_1.loc[i,"datetime"]
        break

# Iterating through the put data till 15:20 unless we reach the limit

for i in range(len(put_data_1)):
    put_time=put_data_1.loc[i,"datetime"].split(" ")[1][0:5].strip()
    if(put_data_1.loc[i,"close"]>put_stop):
        put_stop=put_data_1.loc[i,"close"]
        put_stop_time=put_data_1.loc[i,"datetime"]
        break
    elif(put_time=="15:20"):
        put_stop=put_data_1.loc[i,"close"]
        put_stop_time=put_data_1.loc[i,"datetime"]
        break


print("call_stop {},call_stop_time {}".format(call_stop,call_stop_time))
print("put_stop {},put_stop_time {}".format(put_stop,put_stop_time))
# print(call_start,call_stop,put_start,put_stop)
# print(open_c,open_p)
# print(call_data)
# print("PUT data",put_data)