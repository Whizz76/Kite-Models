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
# logging.info(data)

# Get the access token from the above response and store it in a variable
access_token = ""
kite.set_access_token(access_token)

net = kite.margins()["equity"]["net"]
logging.info("net: {}".format(net))

trade_counter={}
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

exchange1=str(input_values["exchange"]).upper()
exchange2="NFO"
if(exchange1=="BSE"): exchange2="BFO"

margin_range=int(input_values["margin_range"])

# logging.info(entry_time_hour,entry_time_min,exit_time_hour,exit_time_min)
# logging.info(stoploss,trade_size,symbol,trading_symbol,margin_range)
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

future_date = current_date + timedelta(days=7)

result_string = ""

if future_date.month != current_date.month:
    # If yes, add the first three letters of the current month
    result_string=year_last_two_digits+ current_date.strftime("%b").upper()

else:

    if current_date.month<10:
        result_string = year_last_two_digits + month_index.zfill(1) + day.zfill(2)
    # Form the string in the format yymdd
    else: result_string = year_last_two_digits + month_index.zfill(2) + day.zfill(2)


symbol=sym+result_string
logging.info("symbol {}".format(symbol))

def is_current_time(hour, minute):
    # Get current time
    current_time = datetime.now().time()
    
    # Check if current hour and minute match the parameters
    return current_time.hour >= hour and current_time.minute >= minute

# check find the number of lots that can be traded 

def num_lots_fun(sell_sym,buy_sym,trade_size,exchange2):
    # Fetch margin detail for order/orders
    num_lots=0
    order_param_basket=[]
    for sym in sell_sym:
        order_param_basket.append(
            {
                "exchange": exchange2,
                "tradingsymbol": sym,
                "transaction_type": "SELL",
                "variety": "regular",
                "product": "MIS",
                "order_type": "MARKET",
                "quantity": trade_size
            }
        )
    for sym in buy_sym:
        order_param_basket.append(
            {
                "exchange": exchange2,
                "tradingsymbol": sym,
                "transaction_type": "BUY",
                "variety": "regular",
                "product": "MIS",
                "order_type": "MARKET",
                "quantity": trade_size
            }
        )
    try:
        # Fetch margin detail for single order
        margin_net_available = kite.margins()["equity"]["net"]

        margin_detail = kite.basket_order_margins(order_param_basket)
        margin_required = margin_detail["final"]["total"]
        num_lots=int(margin_net_available/margin_required)
        logging.info("Available margin: {} , Required margin: {}".format(margin_net_available,margin_required))   

    except Exception as e:
        logging.info("Error fetching order margin: {}".format(e))

    logging.info("num_lots: {}".format(num_lots))
    return num_lots

# Place an order
def place_order(symbol,direction,exchange,o_type,product,quantity):
    logging.info("placing {} order".format(direction))
    
    try:
        order_id = kite.place_order(tradingsymbol=symbol,
                                    exchange=exchange,
                                    transaction_type=kite.TRANSACTION_TYPE_BUY if direction == "buy" else kite.TRANSACTION_TYPE_SELL,
                                    quantity=quantity,
                                    variety=kite.VARIETY_REGULAR,
                                    order_type=o_type,
                                    product=product)
        logging.info("Order placed. ID is: {}".format(order_id))
        if(direction!="buy"): trade_counter[symbol]+=1
        return order_id
    
    except Exception as e:
        logging.info("Order placement failed: {}".format(e))
        return None

def stoploss_reached(stoposs_id,cur_price,LTP_limit):
    return stoposs_id==None and cur_price>=LTP_limit

# Get the minimum LTP_stoploss_limit
def min_val(cur_price,stoploss,min_ltp):
    lim_ltp=cur_price*(1+stoploss)
    if(lim_ltp<min_ltp): 
        min_ltp=lim_ltp
    return min_ltp

# place stoploss order

def place_stoploss_order(tradingSym,exchange,product,order_type,quantity,direction):

    if(trade_counter[tradingSym]>=3 or is_current_time(13,00)): 
        return None
    
    order=place_order(tradingSym,direction,exchange,order_type,product,quantity)
    time.sleep(1)

    if(order):

        stoploss_orderid=None
        LTP=kite.quote(exchange+":"+tradingSym)[exchange+":"+tradingSym]['last_price']
        limit=LTP*(1+stoploss)
        return stoploss_orderid,limit
    
    else: return None

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
        logging.info("SP: {}".format(SP))
        
        CE_price=SP
        PE_price=SP

        tradingSym_PE=symbol+str(PE_price)+"PE"
        tradingSym_CE=symbol+str(CE_price)+"CE"

        logging.info("PE_sym {}".format(tradingSym_PE))
        logging.info("CE_sym {}".format(tradingSym_CE))

        CE_price=SP+margin_range
        PE_price=SP-margin_range

        tradingSym_PE_margin=symbol+str(PE_price)+"PE"
        tradingSym_CE_margin=symbol+str(CE_price)+"CE"

        sell_sym=[tradingSym_PE,tradingSym_CE]
        buy_sym=[tradingSym_PE_margin,tradingSym_CE_margin]
        num_lots=num_lots_fun(sell_sym,buy_sym,trade_size,exchange2)

        trade_counter[tradingSym_PE]=0
        trade_counter[tradingSym_CE]=0
        trade_counter[tradingSym_PE_margin]=0
        trade_counter[tradingSym_CE_margin]=0

        if(num_lots!=0):
            quantity=trade_size*num_lots

            PE_margin=place_order(tradingSym_PE_margin,"buy",kite_exchange,kite.ORDER_TYPE_MARKET,kite.PRODUCT_MIS,quantity)
            CE_margin=place_order(tradingSym_CE_margin,"buy",kite_exchange,kite.ORDER_TYPE_MARKET,kite.PRODUCT_MIS,quantity)

            PE_LTP=None
            CE_LTP=None

            if(PE_margin and CE_margin): 
                PE_order=place_order(tradingSym_PE,"sell",kite_exchange,kite.ORDER_TYPE_MARKET,kite.PRODUCT_MIS,quantity)
                time.sleep(1)
                if(PE_order): PE_LTP=kite.quote(exchange2+":"+tradingSym_PE)[exchange2+":"+tradingSym_PE]['last_price']

                CE_order=place_order(tradingSym_CE,"sell",kite_exchange,kite.ORDER_TYPE_MARKET,kite.PRODUCT_MIS,quantity)
                time.sleep(1)
                if(CE_order): CE_LTP=kite.quote(exchange2+":"+tradingSym_CE)[exchange2+":"+tradingSym_CE]['last_price']
            
            limit_PE=PE_LTP*(1+stoploss)
            limit_CE=CE_LTP*(1+stoploss)

            PE_stoploss_orderid=None
            CE_stoploss_orderid=None

            while True:

                cur_PE_price=kite.quote(exchange2+":"+tradingSym_PE)[exchange2+":"+tradingSym_PE]['last_price']
                cur_CE_price=kite.quote(exchange2+":"+tradingSym_CE)[exchange2+":"+tradingSym_CE]['last_price']

                limit_PE=min_val(cur_PE_price,stoploss,limit_PE)
                limit_CE=min_val(cur_CE_price,stoploss,limit_CE)


                if is_current_time(exit_time_hour,exit_time_min):

                    if(PE_stoploss_orderid==None): PE_stoploss_orderid=place_order(tradingSym_PE,"buy",kite_exchange,kite.ORDER_TYPE_MARKET,kite.PRODUCT_MIS,quantity)
                    if(CE_stoploss_orderid==None): CE_stoploss_orderid=place_order(tradingSym_CE,"buy",kite_exchange,kite.ORDER_TYPE_MARKET,kite.PRODUCT_MIS,quantity)

                    if(PE_margin): PE_sell_order=place_order(tradingSym_PE_margin,"sell",kite_exchange,kite.ORDER_TYPE_MARKET,kite.PRODUCT_MIS,quantity)
                    if(CE_margin): CE_sell_order=place_order(tradingSym_CE_margin,"sell",kite_exchange,kite.ORDER_TYPE_MARKET,kite.PRODUCT_MIS,quantity)
                    
                    break

                elif(PE_stoploss_orderid!=None and CE_stoploss_orderid!=None):

                    logging.info("stoploss reached, again placing the sell orders....")

                    PE_stoploss_order=place_stoploss_order(tradingSym_PE,kite_exchange,kite.PRODUCT_MIS,kite.ORDER_TYPE_MARKET,quantity,"sell")
                    if(PE_stoploss_order):
                        PE_stoploss_orderid,limit_PE=PE_stoploss_order

                    CE_stoploss_order=place_stoploss_order(tradingSym_CE,kite_exchange,kite.PRODUCT_MIS,kite.ORDER_TYPE_MARKET,quantity,"sell")
                    if(CE_stoploss_order):
                        CE_stoploss_orderid,limit_CE=CE_stoploss_order
                    

                else:
                    PE_stoploss_status=stoploss_reached(PE_stoploss_orderid,cur_PE_price,limit_PE)
                    CE_stoploss_status=stoploss_reached(CE_stoploss_orderid,cur_CE_price,limit_CE)
                    
                    if(PE_stoploss_status): PE_stoploss_orderid=place_order(tradingSym_PE,"buy",kite_exchange,kite.ORDER_TYPE_MARKET,kite.PRODUCT_MIS,quantity)
                    if(CE_stoploss_status): CE_stoploss_orderid=place_order(tradingSym_CE,"buy",kite_exchange,kite.ORDER_TYPE_MARKET,kite.PRODUCT_MIS,quantity)
                            
                time.sleep(1)
                    

        # Fetch all orders
        logging.info("kite orders {}".format(kite.orders()))
        
def main():
    place_order_time(entry_time_hour,entry_time_min)

if __name__=="__main__":
    main()