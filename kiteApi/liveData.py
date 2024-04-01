import logging
from kiteconnect import KiteConnect
import kiteconnect.exceptions
from kiteconnect import KiteTicker
import pandas as pd
from datetime import datetime, timedelta
import json
import requests
import csv

logging.basicConfig(level=logging.DEBUG)

api_key = "t416qxyj6fek1upt"
kite = KiteConnect(api_key=api_key)

# get the request token from "https://kite.trade/connect/login?api_key=xxxxx&v=3" and login.
# data = kite.generate_session("h3PyhDEbw3N5yO7X9WNclOcPpKa6tSjD",api_secret="oc4jdd5sa8k6e7m6r463s898blepehmj")
# print(data)

# Get the access token from the above response and store it in a variable
access_token = "FaA7BWJ1xebOrSL6kfkwNtmHa7OFw8lP"
kite.set_access_token(access_token)

# Get the instrument token for the instrument you want to subscribe to from the instruments list (.csv file)

# kws = KiteTicker(api_key,access_token)
tokens =[260105,256265] # Bank Nifty and Nifty 50
ticker = "NSE:NIFTY BANK"

interval_high = kite.quote(ticker)[ticker]['ohlc']['high']
print("high",interval_high)


interval_low  = kite.quote(ticker)[ticker]['ohlc']['low']
print("low",interval_low)

# Websocket Streaming

kws = KiteTicker(api_key,access_token)
tokens =[260105,256265]
bank_nifty_token=260105
column_names = ["instrument_token","last_price","open","high","low","close","change","timestamp"]

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
    data={"instrument_token":tick["instrument_token"],"last_price":tick["last_price"],"open":tick["ohlc"]["open"],"high":tick["ohlc"]["high"],"low":tick["ohlc"]["low"],"close":tick["ohlc"]["close"],"change":tick["change"],"exchange_timestamp":tick["exchange_timestamp"]}
    update_csv_with_json("liveData.csv", data)
  # logging.debug("Ticks: {}".format(ticks))

def on_connect(ws, response):
  # Subscribe to a list of instrument_tokens
  ws.subscribe([260105])
  ws.set_mode(ws.MODE_FULL,[260105])

def on_close(ws, code, reason):
  # On connection close stop the main loop
  # Reconnection will not happen after executing `ws.stop()`
  ws.stop()

kws.on_ticks = on_ticks
kws.on_connect = on_connect
kws.on_close = on_close
kws.connect()

