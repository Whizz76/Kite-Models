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

def place_order_kite(tradingsymbol,price,quantity,direction,order_type,product,variety,exchange,validity):
    """
    This function will place an order on the exchange
    """
    print("Placing order {} Qty: {} Direction: {}".format(tradingsymbol,quantity,direction))
    try:
        order_id = kite.place_order(tradingsymbol=tradingsymbol,
                                    quantity=quantity,
                                    transaction_type=kite.TRANSACTION_TYPE_BUY if direction == "buy" else kite.TRANSACTION_TYPE_SELL,
                                    order_type=order_type,
                                    product=product,
                                    variety=variety,
                                    price=price,
                                    validity=validity,
                                    exchange=exchange)
        
        logging.info("Order placed. ID is: {}".format(order_id))
        print("Order placement successful. Direction is {} OrderId is: {}".format(direction,order_id))
        return order_id
    except Exception as e:
        logging.info("Order placement failed: {}".format(e.message))

# get_order_id = place_order_kite("NIFTY BANK",0,1,"buy","MARKET","NRML","REGULAR","NSE","DAY")
# print(get_order_id)
# RAJMET-BE