import multiprocessing.process
import pandas as pd
import os
from datetime import datetime, timedelta
import time
import logging
import csv
import multiprocessing

logging.basicConfig(level=logging.DEBUG)

index_data1=pd.read_csv("Bnf_index_data_(16Aug'21To30Aug'22).csv")
index_data2=pd.read_csv("Bnf_index_data_(30Aug'22To30Aug'23).csv")


filename1="BNF_data5_21_22.csv"
filename2="BNF_data6_22_23.csv"
filename="BNF_Aug_21_22_"


# Updating the csv file
column_names=['date','token','stoploss','max_order','net_P&L','time_taken','start_time']

for i in range(1,11):
    column_names.append('Actual_ltp_'+str(i))
    column_names.append("SP_"+str(i))
    column_names.append("SP_time_"+str(i))
    column_names.append("CE_sell_"+str(i))
    column_names.append("PE_sell_"+str(i))
    column_names.append("CE_buy_"+str(i))
    column_names.append("PE_buy_"+str(i))
    column_names.append("start_time_CE_"+str(i))
    column_names.append("start_time_PE_"+str(i))
    column_names.append("end_time_CE_"+str(i))
    column_names.append("end_time_PE_"+str(i))

def update_csv_with_json(csv_file, json_data,column_names):
    """
    Updates the specified CSV file with the provided JSON data.

    Args:
        csv_file (str): Path to the CSV file.
        json_data (dict or list): The JSON data to be written to the CSV.
    """

    with open(csv_file, 'a', newline='') as csvfile:
        csv_writer = csv.writer(csvfile)
        if csvfile.tell() == 0:  # Check if file is empty
            csv_writer.writerow(column_names)
        # Check if the CSV file already has a header row
        try:
            csv_reader = csv.reader(open(csv_file, 'r'))
            next(csv_reader)  # Read and discard the header if it exists
        except StopIteration:
            # Write the header row if the CSV file is empty
            if isinstance(json_data, list) and len(json_data) > 0:
                header_row = json_data[0].keys()
                csv_writer.writerow(header_row)

        # Extract data from the JSON based on its structure (list or dict)
        if isinstance(json_data, list):
            for item in json_data:
                row_data = item.values()
                csv_writer.writerow(row_data)
        elif isinstance(json_data, dict):
            row_data = json_data.values()
            csv_writer.writerow(row_data)
        else:
            raise ValueError("Invalid JSON data format. Expected list or dict.")


# Get the folder names

def get_folder_names(directory,start_y,start_m,start_d,end_y,end_m,end_d):
    folder_names = []
    for entry in os.scandir(directory):
        if entry.is_dir():
            folder_names.append(entry.name)
    # Convert folder names to dates
    dates=[]
    for name in folder_names:
        date=datetime.strptime(name, "%d-%m-%Y")
        if(date.year<start_y or date.year>end_y): continue
        if((date.year==start_y and date.month<start_m) or (date.year==end_y and date.month>end_m)): continue
        if((date.year==start_y and date.month==start_m and date.day<start_d) or 
           (date.year==end_y and date.month==end_m and date.day>end_d)): continue
        date=datetime.strftime(date,"%Y-%m-%d")
        # print(date,name)
        dates.append(date)

    # Sort the dates
    sorted_dates = sorted(dates)
    return sorted_dates

directory = "../Data_BNF/Data_BNF"
sorted_dates1 = get_folder_names(directory,2022,1,7,2022,8,30)
sorted_dates2 = get_folder_names(directory,2022,8,30,2023,8,30)

def initialise_dict():
    data={}
    for key in column_names:
        data[key]=None
    return data

def is_file_present(folder_path, file_name):
    file_path = os.path.join(folder_path, file_name)
    return os.path.exists(file_path)

start_time = datetime.strptime('09:15:00', '%H:%M:%S')
end_time = datetime.strptime('15:15:00', '%H:%M:%S')
end_time1=datetime.strptime('14:00:00', '%H:%M:%S')
time_step = timedelta(minutes=1)
time_step1 = timedelta(minutes=5)  # Assuming 5-minute intervals

# Define the range for stoploss (percentage)
min_percentage = 50
max_percentage = 100
percentage_step = 5  # Assuming 5% intervals

time_values=[]
time_values1=[]
stoploss_values=[]
order_ranges=[]

# Get the trading symbol
token="BNF"
def get_sym(date):
    print(date)
    date=date.split('-')
    s=token+date[0]+date[1]+date[2]
    return s

def get_reverse(test_date):
    test_date=test_date.split('-')
    test_date=test_date[2]+'-'+test_date[1]+'-'+test_date[0]
    return test_date

# Number of numbers after hitting SL for both call and put
# 3-10
for i in range(1,6):
    order_ranges.append(i)
# BNF2021081836100CE
# Storing the time values

current_time = start_time
while current_time <= end_time:
    time_values.append(current_time.strftime("%H:%M:%S"))
    current_time += time_step

current_time = start_time
while current_time <= end_time1:
    time_values1.append(current_time.strftime("%H:%M:%S"))
    current_time += time_step1
# Storing the stoploss values

stoploss_values = list(range(min_percentage, max_percentage + 1, percentage_step))

ratio_limit=0.9
def place_limit_order(cur_price,previous_price):
    ratio=float(cur_price/previous_price)
    return ratio<=ratio_limit

def is_exit_time(time,hr,mn):
    t=datetime.strptime(time,"%H:%M:%S")
    return t.hour>=hr and t.minute>=mn

def limit_order(sorted_dates,filename,index_data,order_range):
    
    for stoploss_val in stoploss_values:
        stoploss=round(0.01*stoploss_val,2)
        for day in sorted_dates:
            filename_exp="../Data_BNF/Data_BNF/"+get_reverse(day)
            if os.path.exists(filename_exp)==False: continue
            for time_val1 in time_values1:
                SP=None
                sl_reached_PE=True
                sl_reached_CE=True
                num_order=0
                net=0
                s=time.time()
                e=s
                data=initialise_dict()
                start=False
                for time_val in time_values:

                    if(time_val==time_val1):
                        start=True
                    if(start==False): continue

                    if(sl_reached_PE and sl_reached_CE):
                        if(num_order>=order_range or (is_exit_time(time_val,13,0) and num_order!=0)): continue
                        SP=index_data[index_data['datetime'].apply(lambda x:x.split(' ')[0].strip()==str(day) and x.split(' ')[1]==time_val)]
                        if(SP.empty==False): 
                            SP=SP.iloc[0]
                            SP=SP['close']
                            actual_ltp=SP
                            SP=int(round(SP,-2))
                            tradingSym_PE=get_sym(day)+str(SP)+"PE"
                            tradingSym_CE=get_sym(day)+str(SP)+"CE"
                        else: SP=None
                        if(SP==None): continue

                        tradingSym_PE=get_sym(day)+str(SP)+"PE"
                        tradingSym_CE=get_sym(day)+str(SP)+"CE"
                        
                        filename_PE="../Data_BNF/Data_BNF/"+get_reverse(day)+"/"+tradingSym_PE+".csv"
                        filename_CE="../Data_BNF/Data_BNF/"+get_reverse(day)+"/"+tradingSym_CE+".csv"

                        if os.path.exists(filename_PE)==False or os.path.exists(filename_CE)==False:
                            continue

                        PE_df=pd.read_csv(filename_PE)
                        CE_df=pd.read_csv(filename_CE)

                        PE_LTP=PE_df[PE_df['datetime'].apply(lambda x:x.split(' ')[0].strip()==str(day) and x.split(' ')[1]==time_val)]
                        CE_LTP=CE_df[CE_df['datetime'].apply(lambda x:x.split(' ')[0].strip()==str(day) and x.split(' ')[1]==time_val)]

                        if(PE_LTP.empty or CE_LTP.empty): continue

                        PE_LTP=(PE_LTP.iloc[0])['close']
                        CE_LTP=(CE_LTP.iloc[0])['close']
                        PE_LTP_og=PE_LTP
                        CE_LTP_og=CE_LTP
                        stoploss_PE=round(PE_LTP*(1+stoploss),1)
                        stoploss_CE=round(CE_LTP*(1+stoploss),1)
                        limit_CE=stoploss_CE
                        limit_PE=stoploss_PE

                        sl_reached_CE=False
                        sl_reached_PE=False
                        num_order+=1

                        data["SP_"+str(num_order)]=SP
                        data['Actual_ltp_'+str(num_order)]=actual_ltp
                        data["SP_time_"+str(num_order)]=time_val
                        data["CE_sell_"+str(num_order)]=CE_LTP_og
                        data["start_time_CE_"+str(num_order)]=time_val
                        data["PE_sell_"+str(num_order)]=PE_LTP_og
                        data["start_time_PE_"+str(num_order)]=time_val

                        continue

                    cur_PE=PE_df[PE_df['datetime'].apply(lambda x:x.split(' ')[0].strip()==str(day) and x.split(' ')[1]==time_val)]
                    cur_CE=CE_df[CE_df['datetime'].apply(lambda x:x.split(' ')[0].strip()==str(day) and x.split(' ')[1]==time_val)]

                    if(cur_PE.empty or cur_CE.empty): continue

                    cur_PE=(cur_PE.iloc[0])['close']
                    cur_CE=(cur_CE.iloc[0])['close']

                    if(sl_reached_PE==False and (cur_PE>=limit_PE or is_exit_time(time_val,15,15))):
                        print("triggered for price {} at {}".format(PE_LTP_og,limit_PE))
                        net+=PE_LTP_og
                        net-=limit_PE
                        sl_reached_PE=True
                        data["PE_buy_"+str(num_order)]=limit_PE
                        data["end_time_PE_"+str(num_order)]=time_val
                        
                    
                    if(sl_reached_CE==False and (cur_CE>=limit_CE or is_exit_time(time_val,15,15))):
                        print("triggered for price {} at {}".format(CE_LTP_og,limit_CE))
                        net+=CE_LTP_og
                        net-=limit_CE
                        sl_reached_CE=True
                        data["CE_buy_"+str(num_order)]=limit_CE
                        data["end_time_CE_"+str(num_order)]=time_val

                    if(sl_reached_PE==False):
                        stoploss_PE=min(round(cur_PE*(1+stoploss),1),stoploss_PE)
                        PE_limit_order=place_limit_order(cur_PE,PE_LTP)
                        if(PE_limit_order):
                            limit_PE=stoploss_PE
                            PE_LTP=cur_PE
                    
                    if(sl_reached_CE==False):
                        stoploss_CE=min(round(cur_CE*(1+stoploss),1),stoploss_CE)
                        CE_limit_order=place_limit_order(cur_CE,CE_LTP)
                        if(CE_limit_order):
                            limit_CE=stoploss_CE
                            CE_LTP=cur_CE
                e=time.time()
                time_elapsed=e-s
                data["date"]=day
                data["token"]=token
                data["stoploss"]=stoploss
                data['max_order']=order_range
                data['net_P&L']=net
                data['time_taken']=time_elapsed
                data['start_time']=time_val1
                # data={'date':day,'token':'BNF','stoploss':stoploss,'max_order':order_range,'net_P&L':net,'time':time_elapsed}
                # print(data)
                # print(time_val)
                update_csv_with_json(filename,data,column_names)
                

if __name__=="__main__":
    p1=multiprocessing.Process(target=limit_order,args=(sorted_dates1,filename+str(1)+'.csv',index_data1,1,))
    p2=multiprocessing.Process(target=limit_order,args=(sorted_dates1,filename+str(2)+'.csv',index_data1,2,))
    p3=multiprocessing.Process(target=limit_order,args=(sorted_dates1,filename+str(3)+'.csv',index_data1,3,))
    p4=multiprocessing.Process(target=limit_order,args=(sorted_dates1,filename+str(4)+'.csv',index_data1,4,))
    # p5=multiprocessing.Process(target=limit_order,args=(sorted_dates1,filename+str(5)+'.csv',index_data1,5,))
    
   

    p1.start()
    p2.start()
    p3.start()
    p4.start()
    # p5.start()
    

    logging.info("Process started with pid %s",p1.pid)
    logging.info("Process started with pid %s",p2.pid)
    logging.info("Process started with pid %s",p3.pid)
    logging.info("Process started with pid %s",p4.pid)
    # logging.info("Process started with pid %s",p5.pid)
    

    p1.join()
    p2.join()
    p3.join()
    p4.join()
    # p5.join()
    # print(initialise_dict())
    # print(sorted_dates1)
   
    


                    

