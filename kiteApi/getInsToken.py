import logging
from kiteconnect import KiteConnect
import kiteconnect.exceptions
from kiteconnect import KiteTicker
import pandas as pd
from datetime import datetime, timedelta
import json
import requests

logging.basicConfig(level=logging.DEBUG)

api_key = "t416qxyj6fek1upt"
kite = KiteConnect(api_key=api_key)

# get the request token from "https://kite.trade/connect/login?api_key=xxxxx&v=3" and login.
# data = kite.generate_session("OEAmdfk1aLKs3Yor3lyxc8b5Sh8qRGzB",api_secret="oc4jdd5sa8k6e7m6r463s898blepehmj")
# print(data)

# Get the access token from the above response and store it in a variable
access_token = "FaA7BWJ1xebOrSL6kfkwNtmHa7OFw8lP"
kite.set_access_token(access_token)


# instruments = kite.instruments(exchange="NSE")
# instruments=pd.json_normalize(instruments)
# print(instruments)
# Store it in a .csv file

# Get the ltp price for a given token
LTP=kite.ltp("NSE:NIFTY BANK")
print(LTP)
# instruments.to_csv("instruments2.csv")