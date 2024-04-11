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
# access_token = "9u1L639cc4SYvh7bG8gpAaUc63V7iRCF"
# kite.set_access_token(access_token)

# net = kite.margins()["equity"]["net"]
# print("net: ",net)


# Initializing the input parameters
# -----------------------------------------------------------------------

input_df=pd.read_csv("input.csv")

entry_time_hour=9
entry_time_min=40

exit_time_hour=15
exit_time_min=15

current_weekday=datetime.now().weekday()
input_values=input_df.loc[current_weekday]

entry_time_hour=int(input_values["entry_time"][0:2])
entry_time_min=int(input_values["entry_time"][-2:])

exit_time_hour=int(input_values["exit_time"][0:2])
exit_time_min=int(input_values["exit_time"][-2:])

stoploss=float(input_values["stoploss"])
trade_size=int(input_values["quantity"])

symbol=str(input_values["instrument_token"]).upper()
sym=str(input_values["trading_symbol"]).upper()

exchange1=str(input_values["exchange1"]).upper()
exchange2="NFO"
if(exchange1=="BSE"): exchange2="BFO"

margin_range=int(input_values["margin_range"])

# print(entry_time_hour,entry_time_min,exit_time_hour,exit_time_min)
# print(stoploss,trade_size,symbol,trading_symbol,margin_range)
# -----------------------------------------------------------------------
kite_exchange=kite.EXCHANGE_NFO
if(exchange2=="BFO"): kite_exchange=kite.EXCHANGE_BFO

temp=exchange1+":"+symbol

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
        logging.info("Order placed. ID is: {}".format(order_id))
        return order_id
    
    except Exception as e:
        logging.info("Order placement failed: {}".format(e))
        return None

def place_order_time(time_hour,time_minute):

    placeOrder=False

    while True:
        if is_current_time(time_hour,time_minute):
            placeOrder=True
            break
        else:
            logging.info("Waiting for the right time to place order")
            time.sleep(1)

    if(placeOrder):

        token_ltp = kite.quote(temp)[temp]['last_price']
        SP=int(round(token_ltp,-2))
        print("SP: ",SP)
        
        CE_price=SP
        PE_price=SP

        tradingSym_PE=symbol+str(PE_price)+"PE"
        tradingSym_CE=symbol+str(CE_price)+"CE"

        print(tradingSym_PE)
        print(tradingSym_CE)

        CE_price=SP+margin_range
        PE_price=SP-margin_range

        tradingSym_PE_margin=symbol+str(PE_price)+"PE"
        tradingSym_CE_margin=symbol+str(CE_price)+"CE"

        PE_margin=place_order(tradingSym_PE_margin,"buy",kite_exchange,kite.ORDER_TYPE_MARKET,kite.PRODUCT_MIS)
        CE_margin=place_order(tradingSym_CE_margin,"buy",kite_exchange,kite.ORDER_TYPE_MARKET,kite.PRODUCT_MIS)

        PE_LTP=None
        CE_LTP=None

        if(PE_margin and CE_margin): 
            PE_order=place_order(tradingSym_PE,"sell",kite_exchange,kite.ORDER_TYPE_MARKET,kite.PRODUCT_MIS)
            time.sleep(1)
            if(PE_order): PE_LTP=kite.quote(exchange2+":"+tradingSym_PE)[exchange2+":"+tradingSym_PE]['last_price']

            CE_order=place_order(tradingSym_CE,"sell",kite_exchange,kite.ORDER_TYPE_MARKET,kite.PRODUCT_MIS)
            time.sleep(1)
            if(CE_order): CE_LTP=kite.quote(exchange2+":"+tradingSym_CE)[exchange2+":"+tradingSym_CE]['last_price']

        PE_stoploss_orderid=None
        CE_stoploss_orderid=None

        while True:

            cur_PE_price=kite.quote(exchange2+":"+tradingSym_PE)[exchange2+":"+tradingSym_PE]['last_price']
            cur_CE_price=kite.quote(exchange2+":"+tradingSym_CE)[exchange2+":"+tradingSym_CE]['last_price']

            if(PE_stoploss_orderid!=None and CE_stoploss_orderid!=None):
                break

            elif is_current_time(exit_time_hour,exit_time_min):

                if(PE_stoploss_orderid==None): PE_stoploss_orderid=place_order(tradingSym_PE,"buy",kite_exchange,kite.ORDER_TYPE_MARKET,kite.PRODUCT_MIS)
                if(CE_stoploss_orderid==None): CE_stoploss_orderid=place_order(tradingSym_CE,"buy",kite_exchange,kite.ORDER_TYPE_MARKET,kite.PRODUCT_MIS)

                if(PE_margin): PE_sell_order=place_order(tradingSym_PE_margin,"sell",kite_exchange,kite.ORDER_TYPE_MARKET,kite.PRODUCT_MIS)
                if(CE_margin): CE_sell_order=place_order(tradingSym_CE_margin,"sell",kite_exchange,kite.ORDER_TYPE_MARKET,kite.PRODUCT_MIS)
                
                break

            else:
                limit=1+stoploss
                if (PE_stoploss_orderid==None and PE_LTP!=None and cur_PE_price>=(PE_LTP*limit)):
                    PE_stoploss_orderid=place_order(tradingSym_PE,"buy",kite_exchange,kite.ORDER_TYPE_MARKET,kite.PRODUCT_MIS)

                if (CE_stoploss_orderid==None and CE_LTP!=None and cur_CE_price>=(CE_LTP*limit)):
                    CE_stoploss_orderid=place_order(tradingSym_CE,"buy",kite_exchange,kite.ORDER_TYPE_MARKET,kite.PRODUCT_MIS)
                    
            time.sleep(1)
                

        # Fetch all orders
        print(kite.orders())
        
def main():
    place_order_time(entry_time_hour,entry_time_min)

if __name__=="__main__":
    main()