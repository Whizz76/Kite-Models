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
# data = kite.generate_session("lFIDlyyFf64QyAEjnyh7OKkvu6aU5KF2",api_secret="oc4jdd5sa8k6e7m6r463s898blepehmj")
# print(data)

# Get the access token from the above response and store it in a variable
access_token = "9u1L639cc4SYvh7bG8gpAaUc63V7iRCF"
kite.set_access_token(access_token)
print(kite.margins())
net = kite.margins()["equity"]["net"]
# live_balance=kite.margins()["equity"]["available"]["live_balance"]
print(net)

from datetime import datetime

# Get current date
current_date = datetime.now()

# Extract year's last two digits
year_last_two_digits = str(current_date.year)[-2:]

# Extract month index
month_index = str(current_date.month)
# Extract day
day = str(current_date.day)

if current_date.month<10:
    result_string = year_last_two_digits + month_index.zfill(1) + day.zfill(2)
# Form the string in the format yymdd
else: result_string = year_last_two_digits + month_index.zfill(2) + day.zfill(2)

sym="NIFTY"

symbol=sym+result_string
temp="NSE:"+symbol
token_ltp=kite.quote(temp)[temp]['last_price']
print(token_ltp)
# # instruments = kite.instruments(exchange="NSE")
# # instruments=pd.json_normalize(instruments)
# # print(instruments)
# # Store it in a .csv file

# # Get the ltp price for a given token
# symbol="NIFTY 50"
# temp="NSE:"+symbol
# token_ltp=kite.quote(temp)[temp]['last_price']
# print(token_ltp)
# SP=int(round(token_ltp,-2))
# # SP=46100
# CE_price=SP
# PE_price=SP
# symbol="NIFTY24404"

# print(kite.quote("NFO:BANKNIFTY24APR46100PE")["NFO:BANKNIFTY24APR46100PE"]['last_price'])

# tradingSym_PE=symbol+str(PE_price)+"PE"
# tradingSym_CE=symbol+str(CE_price)+"CE"

# print(tradingSym_PE)
# print(tradingSym_CE)

# cur_PE_price=kite.quote("NFO:"+tradingSym_PE)["NFO:"+tradingSym_PE]['last_price']
# cur_CE_price=kite.quote("NFO:"+tradingSym_CE)["NFO:"+tradingSym_CE]['last_price']

# print(cur_PE_price)
# print(cur_CE_price)
# print(kite.quote("NFO:"+tradingSym_PE)["NFO:"+tradingSym_PE]['last_price'])
# print(kite.quote("NFO:"+tradingSym_CE)["NFO:"+tradingSym_CE]['last_price'])

# print(tradingSym_PE)
# print(tradingSym_CE)
# tradingSym_CE=symbol+str(PE_price)+"PE"
# token_ltp=kite.quote("NFO:"+tradingSym_PE)["NFO:"+tradingSym_PE]['last_price']
# print(token_ltp)
# tradingSym_CE=symbol+str(CE_price)+"CE"
# token_ltp=kite.quote("NFO:"+tradingSym_CE)["NFO:"+tradingSym_CE]['last_price']
# print(token_ltp)
# instruments.to_csv("instruments2.csv")