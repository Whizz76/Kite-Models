import logging
from kiteconnect import KiteConnect
import kiteconnect.exceptions
from kiteconnect import KiteTicker
import pandas as pd
from datetime import datetime, timedelta,time
import json
import requests

logging.basicConfig(level=logging.DEBUG)

api_key = "t416qxyj6fek1upt"
kite = KiteConnect(api_key=api_key)

# get the request token from "https://kite.trade/connect/login?api_key=xxxxx&v=3" and login.
# data = kite.generate_session("h3PyhDEbw3N5yO7X9WNclOcPpKa6tSjD",api_secret="oc4jdd5sa8k6e7m6r463s898blepehmj")
# print(data)

# Get the access token from the above response and store it in a variable
access_token = "R2TVZ656Lwc0M3Fo9Xo9KQ3g917Klxsy"
kite.set_access_token(access_token)

# # RAJMET-BE

# Place an order
def place_order(symbol,direction,exchange,o_type,product):

    try:
        order_id = kite.place_order(tradingsymbol=symbol,
                                    exchange=exchange,
                                    transaction_type=kite.TRANSACTION_TYPE_BUY if direction == "buy" else kite.TRANSACTION_TYPE_SELL,
                                    quantity=1,
                                    variety=kite.VARIETY_REGULAR,
                                    order_type=o_type,
                                    product=product)
        logging.info("Order placed. ID is: {}".format(order_id))
        return order_id
    
    except Exception as e:
        logging.info("Order placement failed: {}".format(e))
        return None
        

def place_SLM_order(trigger_price,buy_sell):
    try:
        order_id = kite.place_order(tradingsymbol="INFY",
                                    exchange=kite.EXCHANGE_NSE,
                                    transaction_type=kite.TRANSACTION_TYPE_BUY if buy_sell == "buy" else kite.TRANSACTION_TYPE_SELL,
                                    quantity=1,
                                    variety=kite.VARIETY_REGULAR,
                                    order_type=kite.ORDER_TYPE_SLM,
                                    product=kite.PRODUCT_CNC,
                                    trigger_price=trigger_price,
                                    price=0.0)

        logging.info("Order placed. ID is: {}".format(order_id))
        return order_id
    
    except Exception as e:

        logging.info("Order placement failed: {}".format(e))
        return None

def is_current_time_1515():
    # Get the current time
    current_time = datetime.now().time()
    
    # Check if the current time is 15:15 (3:15 PM)
    if current_time.hour == 15 and current_time.minute == 15:
        return True
    else:
        return False



symbol="NIFTY BANK"
temp="NSE:"+symbol
token_ltp = kite.quote(temp)[temp]['last_price']
print(token_ltp)
SP=int(round(token_ltp,-2))
stoploss=0.2

CE_price=SP
PE_price=SP

symbol="BANKNIFTY24410"

tradingSym_PE=symbol+str(PE_price)+"PE"
tradingSym_CE=symbol+str(CE_price)+"CE"

print(tradingSym_PE)
print(tradingSym_CE)

PE_order=place_order(tradingSym_PE,"sell",kite.EXCHANGE_NFO,kite.ORDER_TYPE_MARKET,kite.PRODUCT_MIS)
time.sleep(1)
PE_LTP=kite.quote("NFO:"+tradingSym_PE)["NFO:"+tradingSym_PE]['last_price']

CE_order=place_order(tradingSym_CE,"sell",kite.EXCHANGE_NFO,kite.ORDER_TYPE_MARKET,kite.PRODUCT_MIS)
time.sleep(1)
CE_LTP=kite.quote("NFO:"+tradingSym_CE)["NFO:"+tradingSym_CE]['last_price']

CE_price=SP+1500
PE_price=SP-1500

tradingSym_PE_1500=symbol+str(PE_price)+"PE"
tradingSym_CE_1500=symbol+str(CE_price)+"CE"

if(PE_order): PE_1500=place_order(tradingSym_PE_1500,"buy",kite.EXCHANGE_NFO,kite.ORDER_TYPE_MARKET,kite.PRODUCT_MIS)
if(CE_order): CE_1500=place_order(tradingSym_CE_1500,"buy",kite.EXCHANGE_NFO,kite.ORDER_TYPE_MARKET,kite.PRODUCT_MIS)

PE_stoploss_orderid=None
CE_stoploss_orderid=None

while True:

    cur_PE_price=kite.quote("NFO:"+tradingSym_PE)["NFO:"+tradingSym_PE]['last_price']
    cur_CE_price=kite.quote("NFO:"+tradingSym_CE)["NFO:"+tradingSym_CE]['last_price']

    if(PE_stoploss_orderid!=None and CE_stoploss_orderid!=None):
        break

    elif is_current_time_1515():

        if(PE_stoploss_orderid!=None): PE_stoploss_orderid=place_order(tradingSym_PE,"buy",kite.EXCHANGE_NFO,kite.ORDER_TYPE_MARKET,kite.PRODUCT_MIS)
        if(CE_stoploss_orderid!=None): CE_stoploss_orderid=place_order(tradingSym_CE,"buy",kite.EXCHANGE_NFO,kite.ORDER_TYPE_MARKET,kite.PRODUCT_MIS)
        break

    else:
        if (PE_stoploss_orderid!=None and cur_PE_price>=(PE_LTP*1.2)):
            PE_stoploss_orderid=place_order(tradingSym_PE,"buy",kite.EXCHANGE_NFO,kite.ORDER_TYPE_MARKET,kite.PRODUCT_MIS)

        if (CE_stoploss_orderid!=None and cur_CE_price>=(CE_LTP*1.2)):
            CE_stoploss_orderid=place_order(tradingSym_CE,"buy",kite.EXCHANGE_NFO,kite.ORDER_TYPE_MARKET,kite.PRODUCT_MIS)
            
    time.sleep(1)
        

# Fetch all orders
print(kite.orders())