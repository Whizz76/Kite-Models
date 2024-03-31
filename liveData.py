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
def on_ticks(ws, ticks):
  logging.debug("Ticks: {}".format(ticks))
  print(ticks)


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

