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
access_token = ""
kite.set_access_token(access_token)

instruments = kite.instruments()
instruments=pd.json_normalize(instruments)

instrument_tokens=[]
ticker_name={}
folder_paths={}

def date_to_string(date_object):
    
    # Extract year, month, and day from the datetime object
    year = str(date_object.year)[-2:]  # Extracting last two digits of the year

    if date_object.month<10:
        month = str(date_object.month).zfill(1)
    else: month = str(date_object.month).zfill(2)  # Ensure month is zero-padded if necessary

    
    if date_object.day<10:
        day = str(date_object.day).zfill(1)
    else: day = str(date_object.day).zfill(2)  # Ensure day is zero-padded if necessary
    
    # Concatenate year, month, and day to form the desired string
    date_string = year + month + day
    
    return date_string

def add_token(instrument_tokens,exchange,instrument_token,range_num,symbol,folder_path,expiry_date):
    LTP=kite.quote(exchange+":"+instrument_token)[exchange+":"+instrument_token]["last_price"]
    LTP=int(round(LTP,-2))
    for i in range(LTP-range_num,LTP+range_num+1,100):  
        tradingSym_CE=symbol+str(i)+"CE"
        CE_ticker=int(instruments[instruments["tradingsymbol"]==tradingSym_CE]["instrument_token"].values[0])
        ticker_name[CE_ticker]=tradingSym_CE

        tradingSym_PE=symbol+str(i)+"PE"
        PE_ticker=int(instruments[instruments["tradingsymbol"]==tradingSym_PE]["instrument_token"].values[0])
        ticker_name[PE_ticker]=tradingSym_PE

        instrument_tokens.append(CE_ticker)
        instrument_tokens.append(PE_ticker)

        folder_paths[CE_ticker]=[folder_path,expiry_date]
        folder_paths[PE_ticker]=[folder_path,expiry_date]


# Reading the input parameters from the liveDataCsv.csv file
input_df=pd.read_csv("liveDataCsv.csv")

for i in range(len(input_df)):
    instrument_token=input_df["instrument_token"][i].upper()
    trading_symbol=input_df["trading_symbol"][i].upper()
    exchange=input_df["exchange"][i].upper()

    folder_path=input_df["folder_path"][i].upper()

    range_num=int(input_df["range_num"][i])

    expiry_date=input_df["expiry_date"][i]
    expiry_date_string=date_to_string(expiry_date)

    symbol=trading_symbol+expiry_date_string
    add_token(instrument_tokens,exchange,instrument_token,range_num,symbol,folder_path,expiry_date.strftime("%Y-%m-%d"))


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

  logging.debug("Ticks: {}".format(ticks))

  for tick in ticks:
    data={"timestap":tick["exchange_timestamp"],"symbol":ticker_name[tick["instrument_token"]],"ltp":tick["last_price"],"expiry_date":expiry_date}
    # print(data)
    folder_name1=folder_paths[tick["instrument_token"]][0]
    folder_name2=folder_paths[tick["instrument_token"]][1]
    
    folder_path = os.path.join(folder_name1, folder_name2)
    csv_file_name=ticker_name[tick["instrument_token"]]+".csv"
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