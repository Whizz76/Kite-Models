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
access_token = "FaA7BWJ1xebOrSL6kfkwNtmHa7OFw8lP"
kite.set_access_token(access_token)

# # RAJMET-BE

# Place an order
def place_order(symbol,direction,price,exchange,o_type,product):
    try:
        order_id = kite.place_order(tradingsymbol=symbol,
                                    exchange=exchange,
                                    transaction_type=kite.TRANSACTION_TYPE_BUY if direction == "buy" else kite.TRANSACTION_TYPE_SELL,
                                    quantity=1,
                                    price=price,
                                    variety=kite.VARIETY_REGULAR,
                                    order_type=o_type,
                                    product=product)

        logging.info("Order placed. ID is: {}".format(order_id))
    except Exception as e:
        logging.info("Order placement failed: {}".format(e))
        
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

symbol="BANKNIFTY24APRFUT"
temp="NFO: "+symbol
token_ltp = kite.quote(temp)[temp]['last_price']
SP=int(round(token_ltp,-2))
CE_price=SP
PE_price=SP
tradingSym_PE=symbol+str(PE_price)+"PE"
tradingSym_CE=symbol+str(CE_price)+"CE"

PE_order=place_order(tradingSym_PE,"sell",PE_price,kite.EXCHANGE_NFO,kite.ORDER_TYPE_MARKET,kite.PRODUCT_MIS)
CE_order=place_order(tradingSym_CE,"sell",CE_price,kite.EXCHANGE_NFO,kite.ORDER_TYPE_MARKET,kite.PRODUCT_MIS)

CE_price=SP+1500
PE_price=SP-1500

tradingSym_PE=symbol+str(PE_price)+"PE"
tradingSym_CE=symbol+str(CE_price)+"CE"

if(PE_order): place_order(tradingSym_PE,"buy",PE_price,kite.EXCHANGE_NFO,kite.ORDER_TYPE_MARKET,kite.PRODUCT_MIS)
if(CE_order): place_order(tradingSym_CE,"buy",CE_price,kite.EXCHANGE_NFO,kite.ORDER_TYPE_MARKET,kite.PRODUCT_MIS)


# Fetch all orders
print(kite.orders())