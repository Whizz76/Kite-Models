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

# Check if a file is present within the folder

def is_file_present(folder_path, file_name):
    file_path = os.path.join(folder_path, file_name)
    return os.path.exists(file_path)

profit_values=[5,10,15,20,25,30,35,40,45,50]

# Output data columns

profit_col=[]

for p in profit_values:
    p_data="call_"+str(p)+"%"
    p_time="call_"+str(p)+"%_time"
    profit_col.append(p_data)
    profit_col.append(p_time)

for p in profit_values:
    p_data="put_"+str(p)+"%"
    p_time="put_"+str(p)+"%_time"
    profit_col.append(p_data)
    profit_col.append(p_time)

col1=["date","expiry_date","time","strike_price","actual_strike_price","call_start","put_start"]
columns=col1+profit_col

def check_if_profit(start_price,cur_price):
    profit=((cur_price-start_price)/start_price)*100
    for profit_value in profit_values:
        if(profit>=profit_value and profit<(profit_value+1)):
            key_value=str(profit_value)+"%"
            data_val=profit
            return {key_value:data_val}
    return {}

# Define the range for time
start_time = datetime.strptime('10:30', '%H:%M')
end_time = datetime.strptime('14:30', '%H:%M')
time_step = timedelta(minutes=5)  # Assuming 5-minute intervals

time_values=[]

# Storing the time values

current_time = start_time

while current_time <= end_time:
    time_values.append(current_time.strftime("%H:%M"))
    current_time += time_step

for time in time_values:
    output_data=[]
    output_data_100=[]

    output_df=None
    output_df_100=None

    for it in range(len(index_data)):

        call_profit_data={"5%":None,"10%":None,"15%":None,"20%":None,"25%":None,"30%":None,"35%":None,"40%":None,"45%":None,"50%":None}
        put_profit_data={"5%":None,"10%":None,"15%":None,"20%":None,"25%":None,"30%":None,"35%":None,"40%":None,"45%":None,"50%":None}

        opening_time=index_data.loc[it,"datetime"]
        time_value=opening_time.split(" ")[1][0:5].strip()
        date_value=opening_time.split(" ")[0][0:11].strip()
        # if(datetime.strptime(date_value,"%Y-%m-%d")<=pd.Timestamp('2022-06-01')):
        #     continue
        date='-'.join(reversed(opening_time.split(" ")[0][0:10].split('-')))

        if(datetime.strptime(time,"%H:%M")!=datetime.strptime(time_value,"%H:%M")):
            continue

        # Getting the strike price from the index data
        strike_price=index_data.loc[it,"open"]
        actual_strike_price=strike_price
        strike_price=(int)((strike_price//100)*100)
        strike_price_500=strike_price+500
        # Getting the expiry date

        expiry_date=get_expiry_date(date)
        # print(date,strike_price,expiry_date)
        if(len(expiry_date)==0):
            print("Data Absent")
        else:
            expiry_day=expiry_date
            date=date

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

                    # Iterating through the call data till 14:30 unless we reach the limit

                    for i in range(len(call_data_1)):

                        call_time=call_data_1.loc[i,"datetime"].split(" ")[1][0:5].strip()
                        call_p=call_data_1.loc[i,"close"]

                        # Getting the profit data for the given price
                        return_data=check_if_profit(call_start,call_p)

                        if(return_data):
                            profit_num=list(return_data.keys())[0]
                            profit_val=list(return_data.values())[0]
                            if(call_profit_data[profit_num]!=None):
                                continue
                            else:
                                call_profit_val=[profit_val,call_time]
                                call_profit_data[profit_num]=call_profit_val

                        if(datetime.strptime(call_time,"%H:%M")>datetime.strptime("14:30","%H:%M")):
                            print("call time",call_time)
                            break

                    # Iterating through the put data till 14:30 unless we reach the limit

                    for i in range(len(put_data_1)):
                        put_time=put_data_1.loc[i,"datetime"].split(" ")[1][0:5].strip()
                        put_p=put_data_1.loc[i,"close"]

                        # Getting the profit data for the given price
                        return_data=check_if_profit(put_start,put_p)

                        if(return_data):
                            profit_num=list(return_data.keys())[0]
                            profit_val=list(return_data.values())[0]

                            if(put_profit_data[profit_num]!=None):
                                continue
                            else:
                                put_profit_val=[profit_val,put_time]
                                put_profit_data[profit_num]=put_profit_val

                        if(datetime.strptime(put_time,"%H:%M")>datetime.strptime("14:30","%H:%M")):
                            print("put time",put_time)
                            break


                    # print("call_stop {},call_stop_time {}".format(call_stop,call_stop_time))
                    # print("put_stop {},put_stop_time {}".format(put_stop,put_stop_time))
                    print(time)

                    # Getting the net loss/gain

                    
                    data_output_val=[date,expiry_date,time,strike_price,actual_strike_price,call_start,put_start]

                    for key,val in call_profit_data.items():

                        if val:
                            data_output_val.append(val[0])
                            data_output_val.append(val[1])
                        else:
                            data_output_val.append(None)
                            data_output_val.append(None)
                    
                    for key,val in put_profit_data.items():

                        if val:
                            data_output_val.append(val[0])
                            data_output_val.append(val[1])
                        else:
                            data_output_val.append(None)
                            data_output_val.append(None)
                    
                    if(data_output_val in output_data):
                        continue

                    if(itr==1):
                        output_data_100.append(data_output_val)
                    else:
                        output_data.append(data_output_val)

    output_df=pd.DataFrame(output_data,columns=columns)
    output_df_100=pd.DataFrame(output_data_100,columns=columns)

    folder_path="strategyOutputs/strategy2"

    csv_file_name=f'Jun22_To_Jun23_{time}.csv'
    csv_file_name_100=f'Jun22_To_Jun23_{time}_100.csv'

    csv_file_name=csv_file_name.replace(':','')
    csv_file_name_100=csv_file_name_100.replace(':','')

    output_df.to_csv(os.path.join(folder_path,csv_file_name),index=False)
    output_df_100.to_csv(os.path.join(folder_path,csv_file_name_100),index=False)
