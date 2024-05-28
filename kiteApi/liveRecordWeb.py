import logging
from kiteconnect import KiteConnect
import kiteconnect.exceptions
from kiteconnect import KiteTicker
import pandas as pd
from datetime import datetime, timedelta
import json
import time as time
import requests
import csv
import os

logging.basicConfig(level=logging.DEBUG)

api_key = "t416qxyj6fek1upt"
kite = KiteConnect(api_key=api_key)

# Get the access token from the above response and store it in a variable
access_token = "X1YL6YkaRzKviFoQSlaVHb0sSwkKQNbJ"
kite.set_access_token(access_token)

instruments = kite.instruments()
instruments=pd.json_normalize(instruments)


instrument_tokens=[]
token_data={}

def date_to_string(date_str,is_last_week):
    
    date_object = datetime.strptime(date_str, "%d-%m-%Y")
    # Extract year, month, and day from the datetime object
    year = str(date_object.year)[-2:]  # Extracting last two digits of the year

    if date_object.month<10:
        month = str(date_object.month).zfill(1)
    else: month = str(date_object.month).zfill(2)  # Ensure month is zero-padded if necessary

    
    day = str(date_object.day).zfill(2)  # Ensure day is zero-padded if necessary
    
    # Concatenate year, month, and day to form the desired string
    date_string = year + month + day
    
    if(is_last_week):
        date_string=year+date_object.strftime("%b").upper()
    
    return date_string

def add_token(instrument_tokens,exchange,instrument_token,range_num,symbol,folder_path,expiry_date):
    actual_LTP=kite.quote(exchange+":"+instrument_token)[exchange+":"+instrument_token]["last_price"]
    r=100
    if(str(instrument_token).strip()=="NIFTY" or str(instrument_token).strip()=="FIN NIFTY SERVICE"): r=50
    LTP=round(actual_LTP/r)*r
    print(instrument_token,LTP)
    for i in range(LTP-range_num,LTP+range_num+1,r):  
        tradingSym_CE=symbol+str(i)+"CE"
        CE_ticker=instruments[instruments["tradingsymbol"]==tradingSym_CE]["instrument_token"]

        tradingSym_PE=symbol+str(i)+"PE"
        PE_ticker=instruments[instruments["tradingsymbol"]==tradingSym_PE]["instrument_token"]

        if(CE_ticker.empty or PE_ticker.empty):
            print(instrument_token,tradingSym_CE,tradingSym_PE)
            continue

        CE_ticker=int(CE_ticker.values[0])
        PE_ticker=int(PE_ticker.values[0])

        # print(tradingSym_CE,tradingSym_PE)

        instrument_tokens.append(CE_ticker)
        instrument_tokens.append(PE_ticker)

        token_data[CE_ticker]=[folder_path,expiry_date,tradingSym_CE]
        token_data[PE_ticker]=[folder_path,expiry_date,tradingSym_PE]


# Reading the input parameters from the liveDataCsv.csv file
input_df=pd.read_csv("liveDataCsv.csv")

for i in range(len(input_df)):
    instrument_token=str(input_df["instrument_token"][i]).upper()
    trading_symbol=str(input_df["trading_symbol"][i]).upper()
    exchange=str(input_df["exchange"][i]).upper()

    folder_path=str(input_df["folder_path"][i]).upper()

    range_num=int(input_df["range_num"][i])

    expiry_date=input_df["expiry_date"][i]
    is_last_week=int(input_df["last_week"][i])
    expiry_date_string=date_to_string(expiry_date,is_last_week)
    expiry_date=datetime.strptime(input_df["expiry_date"][i], "%d-%m-%Y")

    index_token=int(instruments[instruments["tradingsymbol"]==instrument_token]["instrument_token"].values[0])
    instrument_tokens.append(index_token)
    token_data[index_token]=[folder_path,expiry_date.strftime("%Y-%m-%d"),instrument_token]

    symbol=trading_symbol+expiry_date_string
    print(expiry_date)
    add_token(instrument_tokens,exchange,instrument_token,range_num,symbol,folder_path,expiry_date.strftime("%Y-%m-%d"))


def create_folder(folder_name,expiry_date):
    folder_path=folder_name
    if not os.path.exists(folder_path):
    # Create the folder
        os.makedirs(folder_path)
        print("Folder created successfully at:", folder_path)
    else:
        print("Folder already exists at:", folder_path)

    folder_path = os.path.join(folder_name, expiry_date)

    # Check if the folder already exists
    if not os.path.exists(folder_path):
        # Create the folder
        os.makedirs(folder_path)
        print("Folder created successfully at:", folder_path)
    else:
        print("Folder already exists at:", folder_path)

kws = KiteTicker(api_key,access_token)

column_names = ["timestamp", "symbol", "ltp", "expiry_date"]

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


def on_ticks(ws, ticks):

#   logging.debug("Ticks: {}".format(ticks))

  for tick in ticks:
    folder_name=token_data[tick["instrument_token"]][0]
    exp_date=token_data[tick["instrument_token"]][1]
    tick_sym=token_data[tick["instrument_token"]][2]
    data={"timestap":tick["exchange_timestamp"],"symbol":tick_sym,"ltp":tick["last_price"],"expiry_date":exp_date}
    # print(data)
    create_folder(folder_name,exp_date)

    folder_path = os.path.join(folder_name, exp_date)
    csv_file_name=tick_sym+".csv"

    update_csv_with_json(os.path.join(folder_path,csv_file_name), data)

def on_connect(ws, response):
  # Subscribe to a list of instrument_tokens
  ws.subscribe(instrument_tokens)
  ws.set_mode(ws.MODE_FULL, instrument_tokens)

def on_close(ws, code, reason):
  # On connection close stop the main loop
  # Reconnection will not happen after executing `ws.stop()`
  ws.stop()

kws.on_ticks = on_ticks
kws.on_connect = on_connect
kws.on_close = on_close
kws.connect()


# print(instruments)