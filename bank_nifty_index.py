from breeze_connect import BreezeConnect
import pandas as pd
import urllib
import os
import datetime

print("https://api.icicidirect.com/apiuser/login?api_key="+urllib.parse.quote_plus("992248823I8852u1321hb780!36n9C06"))

isec = BreezeConnect(api_key="992248823I8852u1321hb780!36n9C06")

isec.generate_session(api_secret="28k11n7t26q!X195)912E3A62048838u", session_token="41206172")
folder_path="outputData"
csv_file_name="BNF_index.csv"
token="CNXBAN"

expiry = "2022-04-21T07:00:00.000Z"

time_interval = "1minute"

# downloading historical data for Nifty
# CNXBAN
# NIFTY
initial=0
def store_data(start_d,end_d):
    global initial

    start_d=start_d+"T09:00:00.000Z"
    end_d=end_d+"T11:00:00.000Z"
    print("start {} end {}".format(start_d,end_d))
    data2 = isec.get_historical_data(interval = time_interval,

                                from_date = start_d,

                                to_date = end_d,

                                stock_code = token,

                                exchange_code = "NSE",

                                product_type = "cash")

    stock_data = pd.DataFrame(data2["Success"])
    if(stock_data.empty==True): return "No data"

    print("Some data")
    folder_path1=folder_path+"/"+csv_file_name

    if(os.path.exists(folder_path1)==True):
        print("File present")
        df=pd.read_csv(folder_path1)
        stock_data=pd.concat([stock_data,df])
    
    stock_data.to_csv(os.path.join(folder_path,csv_file_name),index=False)
    # return stock_data

start_date=datetime.datetime.strptime("2018-06-30","%Y-%m-%d")
end_date=datetime.datetime.strptime("2023-08-30","%Y-%m-%d")
date_step=start_date

print(start_date,end_date)

while(date_step<=end_date):
    start=datetime.datetime.strftime(date_step,"%Y-%m-%d")
    print("date_step and start",date_step,start)
    if(initial==0): store_data(start,start)
    else:
        store_data(start,start)
    date_step+=datetime.timedelta(days=1)
 