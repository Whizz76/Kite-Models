import logging
from kiteconnect import KiteConnect
import kiteconnect.exceptions
from kiteconnect import KiteTicker
import pandas as pd
from datetime import datetime, timedelta
import time as time
import json
import requests
import csv
import os

logging.basicConfig(level=logging.DEBUG)

api_key = "t416qxyj6fek1upt"
kite = KiteConnect(api_key=api_key)

# get the request token from "https://kite.trade/connect/login?api_key=xxxxx&v=3" and login.
# data = kite.generate_session("h3PyhDEbw3N5yO7X9WNclOcPpKa6tSjD",api_secret="oc4jdd5sa8k6e7m6r463s898blepehmj")
# print(data)

# Get the access token from the above response and store it in a variable
access_token = "hwCRIuz9lMxvOEzgo8V8MfzVUlurGxc3"
kite.set_access_token(access_token)

tokens =[260105] # Bank Nifty
ticker = "NSE:NIFTY BANK"

BNF_LTP=kite.quote(ticker)[ticker]['last_price']
BNF_LTP=int(round(BNF_LTP,-2))
print(BNF_LTP)

symbol="BANKNIFTY"

expiry_date = "2024-04-10"
print(expiry_date)

expiry_day=expiry_date[-2:]
expiry_month=expiry_date[5:7]

if(expiry_month[0]=='0'):
    expiry_month=expiry_month[1]

expiry_year=expiry_date[2:4]

symbol=symbol+expiry_year+expiry_month+expiry_day

print(symbol)

column_names = ["timestamp", "symbol", "ltp", "expiry_date"]

def is_current_time(hour, minute):
    # Get current time
    current_time = datetime.now().time()
    
    # Check if current hour and minute match the parameters
    return current_time.hour >= hour and current_time.minute >= minute

def update_csv_with_json(csv_file, json_data):
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
        
current_time=datetime.now().strftime('%Y-%m-%d %H:%M')
print(current_time)
range_num=2500

folder_path="BNF"

if not os.path.exists(folder_path):
    # Create the folder
    os.makedirs(folder_path)
    print("Folder created successfully at:", folder_path)
else:
    print("Folder already exists at:", folder_path)

folder_path = os.path.join("BNF", expiry_date)

# Check if the folder already exists
if not os.path.exists(folder_path):
    # Create the folder
    os.makedirs(folder_path)
    print("Folder created successfully at:", folder_path)
else:
    print("Folder already exists at:", folder_path)

while True:
    if (is_current_time(15,31)):
        break
    if (is_current_time(9,15)):
        
        for i in range(BNF_LTP-range_num,BNF_LTP+range_num+1,100):
            
            tradingSym_CE=symbol+str(i)+"CE"
            tradingSym_PE=symbol+str(i)+"PE"

            csv_file_name_CE=tradingSym_CE+".csv"
            csv_file_name_PE=tradingSym_PE+".csv"

            CE_LTP=kite.quote("NFO:"+tradingSym_CE)["NFO:"+tradingSym_CE]['last_price']
            PE_LTP=kite.quote("NFO:"+tradingSym_PE)["NFO:"+tradingSym_PE]['last_price']

            CE_data={"timestamp":datetime.now().strftime('%Y-%m-%d %H:%M'),"symbol":tradingSym_CE,"ltp":CE_LTP,"expiry_date":expiry_date}
            PE_data={"timestamp":datetime.now().strftime('%Y-%m-%d %H:%M'),"symbol":tradingSym_PE,"ltp":PE_LTP,"expiry_date":expiry_date}

            update_csv_with_json(os.path.join(folder_path,csv_file_name_CE),CE_data)
            update_csv_with_json(os.path.join(folder_path,csv_file_name_PE),PE_data)

    time.sleep(60)
            