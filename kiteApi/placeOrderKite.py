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

# def place_order_kite(tradingsymbol,price,quantity,direction,order_type,product,variety,exchange,validity):
#     """
#     This function will place an order on the exchange
#     """
#     print("Placing order {} Qty: {} Direction: {}".format(tradingsymbol,quantity,direction))
#     try:
#         order_id = kite.place_order(tradingsymbol=tradingsymbol,
#                                     quantity=quantity,
#                                     transaction_type=kite.TRANSACTION_TYPE_BUY if direction == "buy" else kite.TRANSACTION_TYPE_SELL,
#                                     order_type=order_type,
#                                     product=product,
#                                     variety=variety,
#                                     price=price,
#                                     validity=validity,
#                                     exchange=exchange)
        
#         logging.info("Order placed. ID is: {}".format(order_id))
#         print("Order placement successful. Direction is {} OrderId is: {}".format(direction,order_id))
#         return order_id
#     except Exception as e:
#         logging.info("Order placement failed: {}".format(e.message))

# get_order_id = place_order_kite("RAJMET-BE",0,1,"buy","MARKET","NRML","REGULAR","BSE","DAY")
# print(get_order_id)
# print(kite.orders())
# # RAJMET-BE

# Place an order
def place_order():
    try:
        order_id = kite.place_order(tradingsymbol="INFY",
                                    exchange=kite.EXCHANGE_NSE,
                                    transaction_type=kite.TRANSACTION_TYPE_BUY,
                                    quantity=1,
                                    variety=kite.VARIETY_REGULAR,
                                    order_type=kite.ORDER_TYPE_MARKET,
                                    product=kite.PRODUCT_CNC)

        logging.info("Order placed. ID is: {}".format(order_id))
    except Exception as e:
        logging.info("Order placement failed: {}".format(e))
# try:
#     order_id = kite.place_order(tradingsymbol="INFY",
#                                 exchange=kite.EXCHANGE_BSE,
#                                 transaction_type=kite.TRANSACTION_TYPE_BUY,
#                                 quantity=1,
#                                 variety=kite.VARIETY_REGULAR,
#                                 order_type=kite.ORDER_TYPE_MARKET,
#                                 product=kite.PRODUCT_CNC)

#     logging.info("Order placed. ID is: {}".format(order_id))
# except Exception as e:
#     logging.info("Order placement failed: {}".format(e))
        
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
    except Exception as e:
        logging.info("Order placement failed: {}".format(e))

symbol="ITC24APRFUT"
temp="NFO: "+symbol
itc_ltp = kite.quote(temp)[temp]['last_price']
SP=int(round(itc_ltp,-2))
SP_1500=SP+1500

tradingSym=symbol+str(SP_1500)+"CE"


# Fetch all orders
print(kite.orders())