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
# data = kite.generate_session("h3PyhDEbw3N5yO7X9WNclOcPpKa6tSjD",api_secret="oc4jdd5sa8k6e7m6r463s898blepehmj")
# print(data)

# Get the access token from the above response and store it in a variable
access_token = "mf2F4NPeSIjBd4U4k0RF9mYv1C84oSNX"
kite.set_access_token(access_token)


bank_nifty_token=260105
nifty_token=256265

def historical_data(int_token, from_date, to_date, interval):
    """
    This function will return historical data of the instrument for specific period of days for specific interval
    """
    
    df = pd.DataFrame()   
    #the function we defined above which will return token no. of instrument
    
    to_date   = pd.Timestamp(to_date)
    from_date = pd.Timestamp(from_date)

    while True:
        if from_date >= (to_date - timedelta(60)):                     #if from_date is within the 60 days limit
            df = pd.DataFrame(kite.historical_data(int_token, from_date, to_date, interval))
            break
            
        else:                                                            #if from_date has more than 60 days limit
            to_date_new = from_date + timedelta(60)
            
            df = pd.DataFrame(kite.historical_data(int_token, from_date, to_date_new, interval))
            
            #to_date = from_date.date() + dt.timedelta(60)
            from_date = to_date_new
            
    return df

bank_Nifty=historical_data(bank_nifty_token,'01-01-2021','28-02-2021','minute')

# req = "https://api.kite.trade/instruments/historical/260105/minute?from=2022-01-03&to=2022-01-04&api_key=" + api_key + "&access_token=" + access_token
# response = requests.get(req)
# print(response)
# data_ticker = response.json()['data']['candles']
# print(data_ticker)

