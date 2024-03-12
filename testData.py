import pandas as pd
import os
from datetime import datetime, timedelta
import calendar

# Reading the index_data

index_data=pd.read_csv("Bnf_index_data_com1.csv")

# Output data
output={"date":[],"strike_price":[],"call_start":[],"call_stop":[],"put_start":[],"put_stop":[],
                          "net":[],"net_loss":[],"net_gain":[]}
output_data=pd.DataFrame(output)

check_if_done={}

# Get the folder names

def get_folder_names(directory):
    folder_names = []
    for entry in os.scandir(directory):
        if entry.is_dir():
            folder_names.append(entry.name)
    # Convert folder names to dates
    dates = [datetime.strptime(name, "%d-%m-%Y") for name in folder_names]

    # Sort the dates
    sorted_dates = sorted(dates)
    return sorted_dates

directory = "../Data_BNF/Data_BNF"
sorted_dates = get_folder_names(directory)


# Get the expiry date

def get_expiry_date(input_date):
    for date in sorted_dates:
        in_date=datetime.strptime(input_date,"%d-%m-%Y")
        if(date>=in_date):
            # print(date.strftime("%d-%m-%Y"))
            return date.strftime("%d-%m-%Y")
    return ""

def is_file_present(folder_path, file_name):
    file_path = os.path.join(folder_path, file_name)
    return os.path.exists(file_path)

total_net=0
# Getting the output data

for it in range(len(index_data)):

    opening_time=index_data.loc[it,"datetime"]
    time=opening_time.split(" ")[1][0:5].strip()
    date='-'.join(reversed(opening_time.split(" ")[0][0:10].split('-')))

    if(date in check_if_done and check_if_done[date]):
        continue

    elif(time[0:2]=="10"): # Opening time=10.XX AM

        # Get the strike price

        strike_price=index_data.loc[it,"open"]
        strike_price=(int)((strike_price//1000)*1000)
        strike_price_500=(int)(strike_price+500.0)
        check_if_done[date]=True

        # Getting the expiry date

        expiry_date=get_expiry_date(date)

        if(len(expiry_date)==0):
            print("Data Absent")
        else:
            print(date)
            expiry_day=expiry_date
            date=date
            # reversed_day=''.join(reversed(day))

            input_date=expiry_day.split("-")
            input_date_string=''.join(reversed(input_date))
            reversed_day='-'.join(reversed(date.split("-")))

            for itr in range(0,2):
                if (itr==1):
                    strike_price=strike_price_500

                call_path="BNF"+input_date_string+str(strike_price)+"CE.csv"
                put_path="BNF"+input_date_string+str(strike_price)+"PE.csv"
                folder_path="../Data_BNF/Data_BNF/"+expiry_day
                # print(folder_path,put_path,call_path)

                if(is_file_present(folder_path,call_path) and is_file_present(folder_path,put_path)):

                    # print("Entered")

                    # Reading the call and put data

                    call_data=pd.read_csv("../Data_BNF/Data_BNF/"+expiry_day+"/BNF"+input_date_string+str(strike_price)+"CE.csv")
                    put_data=pd.read_csv("../Data_BNF/Data_BNF/"+expiry_day+"/BNF"+input_date_string+str(strike_price)+"PE.csv")

                    # Getting the call and put data during the start i.e here from 10 AM

                    open_c=call_data[call_data["datetime"].str.contains(reversed_day+" 1")]
                    open_p=put_data[put_data["datetime"].str.contains(reversed_day+" 1")]



                    if(len(open_c)==0 or len(open_p)==0):
                        continue
                    if(date=="03-01-2022"):
                        print(call_path,folder_path)
                        print("open_c ",open_c)

                    open_c=open_c.iloc[0]
                    open_p=open_p.iloc[0]

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

                    # print("call_start {},call_stop {},put_start {},put_stop {}".format(call_start,call_stop,put_start,put_stop))

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


                    # print("call_stop {},call_stop_time {}".format(call_stop,call_stop_time))
                    # print("put_stop {},put_stop_time {}".format(put_stop,put_stop_time))

                    # Getting the net loss/gain

                    net=(call_start-call_stop)+(put_start-put_stop)
                    total_net+=net
                    net_loss=None
                    net_gain=None
                    if(net<0):
                        net_loss=net
                    elif (net>0):
                        net_gain=net

                    # Creating the output_data
                    ind=len(output_data)
                    output_data.loc[ind,"date"]=opening_time
                    output_data.loc[ind,"actual_strike_price"]=index_data.loc[it,"open"]
                    output_data.loc[ind,"strike_price"]=strike_price
                    output_data.loc[ind,"expiry_date"]=expiry_date
                    output_data.loc[ind,"call_start"]=call_start
                    output_data.loc[ind,"call_stop"]=call_stop
                    output_data.loc[ind,"put_start"]=put_start
                    output_data.loc[ind,"put_stop"]=put_stop
                    output_data.loc[ind,"net"]=net
                    output_data.loc[ind,"net_loss"]=net_loss
                    output_data.loc[ind,"net_gain"]=net_gain
print(output_data)
output_data.to_csv(index=False)
output_data.to_csv("data"+str(stoploss*100)+".csv")
print(total_net)
# 8258.07500000001