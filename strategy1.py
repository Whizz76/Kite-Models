import pandas as pd
import os
from datetime import datetime, timedelta

df1=pd.read_csv("Bnf_index_data_(16Aug'21To30Aug'22).csv")
df2=pd.read_csv("Bnf_index_data_(30Aug'22To30Aug'23).csv")

df1["date_col"]=df1["datetime"]
df1=df1[df1["date_col"].apply(lambda x:datetime.strptime(x.split(" ")[0][0:11],"%Y-%m-%d"))>=pd.Timestamp('2022-06-01')].reset_index(drop=True)
df1.drop('date_col', axis=1, inplace=True)

index_data=pd.concat([df1, df2], ignore_index=True)
index_data.reset_index(drop=True, inplace=True)
print(index_data)
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
        if(date==in_date):
            # print(date.strftime("%d-%m-%Y"))
            return date.strftime("%d-%m-%Y")
    return ""

def is_file_present(folder_path, file_name):
    file_path = os.path.join(folder_path, file_name)
    return os.path.exists(file_path)

check_if_done={}
stoploss=0.3
output_data=[]
output_data_100=[]
output_df=None
output_df_100=None

for it in range(len(index_data)):
    opening_time=index_data.loc[it,"datetime"]
    time=opening_time.split(" ")[1][0:5].strip()
    date='-'.join(reversed(opening_time.split(" ")[0][0:10].split('-')))

    if(date in check_if_done and check_if_done[date]):
        continue

    if(datetime.strptime(time,"%H:%M")!=datetime.strptime("10:20","%H:%M")):
        continue

    else:
        print(date,time)

    check_if_done[date]=True
    strike_price=index_data.loc[it,"open"]
    actual_strike_price=strike_price
    strike_price=(int)((strike_price//100)*100)
    strike_price_500=(int)(strike_price+500)

    expiry_date=get_expiry_date(date)

    if(len(expiry_date)==0):
        print(date,"Data Absent")
        continue
    
    expiry_day=expiry_date
    date=date
    print(expiry_date)
    input_date=expiry_day.split("-")
    input_date_string=''.join(reversed(input_date))
    reversed_day='-'.join(reversed(date.split("-")))
    folder_path="../Data_BNF/Data_BNF/"+expiry_day

    price=strike_price

    # Getting the ranges for strike price

    for it in range(0,5):
        strike_price=price-(it*100)
        call_path="BNF"+input_date_string+str(strike_price)+"CE.csv"
        put_path="BNF"+input_date_string+str(strike_price)+"PE.csv"
        if(is_file_present(folder_path,call_path) and is_file_present(folder_path,put_path)):
            break

    for it in range(1,6):
        strike_price_500=price+(it*100)
        call_path="BNF"+input_date_string+str(strike_price_500)+"CE.csv"
        put_path="BNF"+input_date_string+str(strike_price_500)+"PE.csv"
        if(is_file_present(folder_path,call_path) and is_file_present(folder_path,put_path)):
            break
    
    for itr in range(0,2):
        if (itr==1):
            strike_price=strike_price_500

        call_path="BNF"+input_date_string+str(strike_price)+"CE.csv"
        put_path="BNF"+input_date_string+str(strike_price)+"PE.csv"
        # print(folder_path,put_path,call_path)

        if(is_file_present(folder_path,call_path) and is_file_present(folder_path,put_path)):

            # print("Entered")

            # Reading the call and put data

            call_data=pd.read_csv("../Data_BNF/Data_BNF/"+expiry_day+"/BNF"+input_date_string+str(strike_price)+"CE.csv")
            put_data=pd.read_csv("../Data_BNF/Data_BNF/"+expiry_day+"/BNF"+input_date_string+str(strike_price)+"PE.csv")

            # Getting the call and put data during the start i.e here from 10 AM

            open_c=call_data[call_data["datetime"].str.contains(reversed_day+" "+time)]
            open_p=put_data[put_data["datetime"].str.contains(reversed_day+" "+time)]

            # print(reversed_day+" "+time)
            if(len(open_c)==0 or len(open_p)==0):
                continue
            open_c=open_c.iloc[0]
            open_p=open_p.iloc[0]

            # Getting the price during the start for both call and put 
                
            call_start=open_c["close"]
            put_start=open_p["close"]

            # Setting the closing prices for both call and put

            call_stop=call_start*(1+stoploss)
            put_stop=put_start*(1+stoploss)

            open_c=call_data[call_data["datetime"].str.contains(reversed_day)]
            open_p=put_data[put_data["datetime"].str.contains(reversed_day)]

            # Getting the call and put data on that particular day after 10 AM

            call_data_1=open_c[open_c['datetime'].apply(lambda x: datetime.strptime(x.split(' ')[1][0:5],"%H:%M")) >= datetime.strptime(time,"%H:%M")]
            put_data_1=open_p[open_p['datetime'].apply(lambda x: datetime.strptime(x.split(' ')[1][0:5],"%H:%M")) >= datetime.strptime(time,"%H:%M")]
            call_data_1=call_data_1.reset_index(drop=True)
            put_data_1=put_data_1.reset_index(drop=True)

            # Setting the stop time for call and put

            call_stop_time=None
            put_stop_time=None

            # Iterating through the call data till 15:20 unless we reach the limit

            for i in range(len(call_data_1)):
                call_time=call_data_1.loc[i,"datetime"].split(" ")[1][0:5].strip()
                if(call_data_1.loc[i,"close"]>=call_stop):
                    call_stop=call_data_1.loc[i,"close"]
                    call_stop_time=call_data_1.loc[i,"datetime"]
                    break
                elif(call_time=="15:15"):
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
                elif(put_time=="15:15"):
                    put_stop=put_data_1.loc[i,"close"]
                    put_stop_time=put_data_1.loc[i,"datetime"]
                    break


            # print("call_stop {},call_stop_time {}".format(call_stop,call_stop_time))
            # print("put_stop {},put_stop_time {}".format(put_stop,put_stop_time))

            # Getting the net loss/gain

            net=(call_start-call_stop)+(put_start-put_stop)
            net_loss=None
            net_gain=None
            net_profit_call_20=None
            net_profit_put_20=None
            percent_gain_call=None
            percent_gain_put=None

            if(call_start>=(1.25*call_stop) and call_start<=(1.33*call_stop)):
                net_profit_call_20=(call_start-call_stop)/call_start
                net_profit_call_20*=100
            
            if(put_start>=(1.25*put_stop) and put_start<=(1.33*put_stop)):
                net_profit_put_20=(put_start-put_stop)/put_start
                net_profit_put_20*=100

            if(call_start>=call_stop):
                percent_gain_call=(call_start-call_stop)/call_start
                percent_gain_call*=100

            if(put_start>=put_stop):
                percent_gain_put=(put_start-put_stop)/put_start
                percent_gain_put*=100

            if(net<0):
                net_loss=net
            elif (net>0):
                net_gain=net

            out_data_val=[date,expiry_date,time,stoploss,strike_price,actual_strike_price,call_start,call_stop,call_stop_time,
                                put_start,put_stop,put_stop_time,net,net_gain,net_loss,net_profit_call_20,
                                net_profit_put_20,percent_gain_call,percent_gain_put]
            if(out_data_val in output_data):
                continue
            print(net,time,stoploss)
            if(itr==1):
                output_data_100.append(out_data_val)
            else:
                output_data.append(out_data_val)



columns=["date","expiry_date","time","stoploss","strike_price","actual_strike_price","call_start","call_stop","call_stop_time","put_start",
                                            "put_stop","put_stop_time","net","net_gain","net_loss","net_profit_call_20",
                                "net_profit_put_20","percent_gain_call","percent_gain_put"]
                        
output_df=pd.DataFrame(output_data,columns=columns)
output_df_100=pd.DataFrame(output_data_100,columns=columns)
folder_path="strategyOutputs"
csv_file_name="strategy1.csv"
csv_file_name_100="strategy1_100.csv"
output_df.to_csv(os.path.join(folder_path,csv_file_name),index=False)
output_df_100.to_csv(os.path.join(folder_path,csv_file_name_100),index=False)

    



    
    
