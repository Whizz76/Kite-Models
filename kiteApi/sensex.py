import logging
from kiteconnect import KiteConnect
import kiteconnect.exceptions
from kiteconnect import KiteTicker
import pandas as pd
from datetime import datetime, timedelta
import time as time
import json
import requests

logging.basicConfig(level=logging.DEBUG)

api_key = "t416qxyj6fek1upt"
kite = KiteConnect(api_key=api_key)

# get the request token from "https://kite.trade/connect/login?api_key=xxxxx&v=3" and login.
# data = kite.generate_session("h3PyhDEbw3N5yO7X9WNclOcPpKa6tSjD",api_secret="oc4jdd5sa8k6e7m6r463s898blepehmj")
# print(data)

# Get the access token from the above response and store it in a variable
access_token = "9u1L639cc4SYvh7bG8gpAaUc63V7iRCF"
kite.set_access_token(access_token)

net = kite.margins()["equity"]["net"]
print(net)

symbol="SENSEX"
temp="BSE:"+symbol
stoploss=0.3

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

sym="SENSEX"
trade_size=60

symbol=sym+result_string
print("symbol",symbol)

def is_current_time(hour, minute):
    # Get current time
    current_time = datetime.now().time()
    
    # Check if current hour and minute match the parameters
    return current_time.hour == hour and current_time.minute >= minute


# Place an order
def place_order(symbol,direction,exchange,o_type,product):

    try:
        order_id = kite.place_order(tradingsymbol=symbol,
                                    exchange=exchange,
                                    transaction_type=kite.TRANSACTION_TYPE_BUY if direction == "buy" else kite.TRANSACTION_TYPE_SELL,
                                    quantity=trade_size,
                                    variety=kite.VARIETY_REGULAR,
                                    order_type=o_type,
                                    product=product)
        logging.iBFO("Order placed. ID is: {}".format(order_id))
        return order_id
    
    except Exception as e:
        logging.iBFO("Order placement failed: {}".format(e))
        return None

def place_order_time(time_hour,time_minute):

    placeOrder=False

    while True:
        if is_current_time(time_hour,time_minute):
            placeOrder=True
            break
        else:
            logging.iBFO("Waiting for the right time to place order")
            time.sleep(1)

    if(placeOrder):

        token_ltp = kite.quote(temp)[temp]['last_price']
        SP=int(round(token_ltp,-2))
        print("SNX SP",SP)
        CE_price=SP
        PE_price=SP

        tradingSym_PE=symbol+str(PE_price)+"PE"
        tradingSym_CE=symbol+str(CE_price)+"CE"

        print(tradingSym_PE)
        print(tradingSym_CE)

        CE_price=SP+3000
        PE_price=SP-3000

        tradingSym_PE_3000=symbol+str(PE_price)+"PE"
        tradingSym_CE_3000=symbol+str(CE_price)+"CE"

        PE_3000=place_order(tradingSym_PE_3000,"buy",kite.EXCHANGE_BFO,kite.ORDER_TYPE_MARKET,kite.PRODUCT_MIS)
        CE_3000=place_order(tradingSym_CE_3000,"buy",kite.EXCHANGE_BFO,kite.ORDER_TYPE_MARKET,kite.PRODUCT_MIS)

        PE_LTP=None
        CE_LTP=None

        if(PE_3000 and CE_3000): 
            PE_order=place_order(tradingSym_PE,"sell",kite.EXCHANGE_BFO,kite.ORDER_TYPE_MARKET,kite.PRODUCT_MIS)
            time.sleep(1)
            if(PE_order): PE_LTP=kite.quote("BFO:"+tradingSym_PE)["BFO:"+tradingSym_PE]['last_price']

            CE_order=place_order(tradingSym_CE,"sell",kite.EXCHANGE_BFO,kite.ORDER_TYPE_MARKET,kite.PRODUCT_MIS)
            time.sleep(1)
            if(CE_order): CE_LTP=kite.quote("BFO:"+tradingSym_CE)["BFO:"+tradingSym_CE]['last_price']

        PE_stoploss_orderid=None
        CE_stoploss_orderid=None

        while True:

            cur_PE_price=kite.quote("BFO:"+tradingSym_PE)["BFO:"+tradingSym_PE]['last_price']
            cur_CE_price=kite.quote("BFO:"+tradingSym_CE)["BFO:"+tradingSym_CE]['last_price']

            if(PE_stoploss_orderid!=None and CE_stoploss_orderid!=None):
                break

            elif is_current_time(15,18):

                if(PE_stoploss_orderid==None): PE_stoploss_orderid=place_order(tradingSym_PE,"buy",kite.EXCHANGE_BFO,kite.ORDER_TYPE_MARKET,kite.PRODUCT_MIS)
                if(CE_stoploss_orderid==None): CE_stoploss_orderid=place_order(tradingSym_CE,"buy",kite.EXCHANGE_BFO,kite.ORDER_TYPE_MARKET,kite.PRODUCT_MIS)

                if(PE_3000): PE_sell_order=place_order(tradingSym_PE_3000,"sell",kite.EXCHANGE_BFO,kite.ORDER_TYPE_MARKET,kite.PRODUCT_MIS)
                if(CE_3000): CE_sell_order=place_order(tradingSym_CE_3000,"sell",kite.EXCHANGE_BFO,kite.ORDER_TYPE_MARKET,kite.PRODUCT_MIS)
                
                break

            else:
                limit=1+stoploss
                if (PE_stoploss_orderid==None and PE_LTP!=None and cur_PE_price>=(PE_LTP*limit)):
                    PE_stoploss_orderid=place_order(tradingSym_PE,"buy",kite.EXCHANGE_BFO,kite.ORDER_TYPE_MARKET,kite.PRODUCT_MIS)

                if (CE_stoploss_orderid==None and CE_LTP!=None and cur_CE_price>=(CE_LTP*limit)):
                    CE_stoploss_orderid=place_order(tradingSym_CE,"buy",kite.EXCHANGE_BFO,kite.ORDER_TYPE_MARKET,kite.PRODUCT_MIS)
                    
            time.sleep(1)
                

        # Fetch all orders
        print(kite.orders())
        
def main():
    place_order_time(9,40)

if __name__=="__main__":
    main()