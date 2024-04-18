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
print("started...")
add_num=0 # add_num is used to add the number of days to the current date
api_key = "t416qxyj6fek1upt"
kite = KiteConnect(api_key=api_key)
test_data={}
# get the request token from "https://kite.trade/connect/login?api_key=xxxxx&v=3" and login.
# data = kite.generate_session("h3PyhDEbw3N5yO7X9WNclOcPpKa6tSjD",api_secret="oc4jdd5sa8k6e7m6r463s898blepehmj")
# logging.info(data)

# Get the access token from the above response and store it in a variable
access_token = "V3I6bMTB3VLC50wILVV8eznOK1m4DF6g"
kite.set_access_token(access_token)
expiry_date="2024-04-18"

net = kite.margins()["equity"]["net"]
logging.info("net: {}".format(net))

# Initializing the input parameters
# -----------------------------------------------------------------------

input_df=pd.read_csv("input.csv")

entry_time_hour=9
entry_time_min=40

exit_time_hour=15
exit_time_min=15

current_weekday=(datetime.now().weekday()+add_num)%7
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
day = str(current_date.day+add_num) 

if current_date.month<10:
    result_string = year_last_two_digits + month_index.zfill(1) + day.zfill(2)
# Form the string in the format yymdd
else: result_string = year_last_two_digits + month_index.zfill(2) + day.zfill(2)


symbol=sym+result_string
logging.info("symbol {}".format(symbol))

def get_current_time():
    # Get current time
    time_difference = timedelta(hours=5, minutes=29)
    return datetime.now()+time_difference

def is_current_time(hour, minute):
    # Get current time
    current_time = get_current_time()
    
    # Check if current hour and minute match the parameters
    if(hour==9): return current_time.hour == hour and current_time.minute >= minute and current_time.second>=26
    else: return current_time.hour == hour and current_time.minute >= minute

def stoploss_reached(stoposs_id,cur_price,LTP_limit):
    return stoposs_id==None and cur_price>=LTP_limit

def get_ltp(trading_symbol):
    BNF_file=pd.read_csv("./BNF/"+expiry_date+"/"+trading_symbol+".csv")
    cur_time=get_current_time().strftime("%H:%M:%S")
    BNF_file=BNF_file[BNF_file["timestamp"]=="2024-04-09 "+cur_time]
    if(not BNF_file.empty): 
        BNF_file=BNF_file.values[0]
        return float(BNF_file[2])
    else: return 0
    
def place_order(tradingSym,transaction_type,exchange,order_type,product):
    BNF_file=pd.read_csv("./BNF/"+expiry_date+"/"+tradingSym+".csv")
    cur_time=get_current_time().strftime("%H:%M:%S")
    BNF_file=BNF_file[BNF_file["timestamp"]=="2024-04-09 "+cur_time]
    if(not BNF_file.empty):
        BNF_file=BNF_file.values[0]
        print(BNF_file[0])
        logging.info("direction: {} price {} symbol {}".format(transaction_type,BNF_file[2],tradingSym))
        return float(BNF_file[2])
    else: return None

def sell(tradingSym):
    BNF_file=pd.read_csv("./BNF/"+expiry_date+"/"+tradingSym+".csv")
    sell_LTP=BNF_file[BNF_file["timestamp"].str.contains("2024-04-09 15:18")].iloc[0]
    print("sell order {} price {}".format(tradingSym,sell_LTP["ltp"]))
    return float(sell_LTP["ltp"])

# Get the minimum LTP_stoploss_limit
def min_val(cur_price,stoploss,min_ltp):
    lim_ltp=cur_price*(1+stoploss)
    if(lim_ltp<min_ltp): 
        min_ltp=lim_ltp
    return min_ltp

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
        
        PE_margin=place_order(tradingSym_PE_margin,"buy",kite_exchange,kite.ORDER_TYPE_MARKET,kite.PRODUCT_MIS)
        CE_margin=place_order(tradingSym_CE_margin,"buy",kite_exchange,kite.ORDER_TYPE_MARKET,kite.PRODUCT_MIS)
        test_data["PE_margin_buy"]=PE_margin
        test_data["CE_margin_buy"]=CE_margin
        
        PE_LTP=None
        CE_LTP=None

        if(PE_margin and CE_margin): 
            PE_order=place_order(tradingSym_PE,"sell",kite_exchange,kite.ORDER_TYPE_MARKET,kite.PRODUCT_MIS)
            time.sleep(1)
            if(PE_order): PE_LTP=get_ltp(tradingSym_PE)

            CE_order=place_order(tradingSym_CE,"sell",kite_exchange,kite.ORDER_TYPE_MARKET,kite.PRODUCT_MIS)
            time.sleep(1)
            if(CE_order): CE_LTP=get_ltp(tradingSym_CE)

        test_data["PE_sell"]=PE_LTP
        test_data["CE_sell"]=CE_LTP
        
        limit_PE=PE_LTP*(1+stoploss)
        limit_CE=CE_LTP*(1+stoploss)


        PE_stoploss_orderid=None
        CE_stoploss_orderid=None

        while True:

            cur_PE_price=get_ltp(tradingSym_PE)
            cur_CE_price=get_ltp(tradingSym_CE)

            limit_PE=min_val(cur_PE_price,stoploss,limit_PE)
            limit_CE=min_val(cur_CE_price,stoploss,limit_CE)

            if is_current_time(exit_time_hour,exit_time_min):

                if(PE_stoploss_orderid==None): PE_stoploss_orderid=place_order(tradingSym_PE,"buy",kite_exchange,kite.ORDER_TYPE_MARKET,kite.PRODUCT_MIS)
                if(CE_stoploss_orderid==None): CE_stoploss_orderid=place_order(tradingSym_CE,"buy",kite_exchange,kite.ORDER_TYPE_MARKET,kite.PRODUCT_MIS)

                if(PE_margin): PE_sell_order=sell(tradingSym_PE_margin)
                if(CE_margin): CE_sell_order=sell(tradingSym_CE_margin)

                test_data["PE_buy"]=PE_stoploss_orderid
                test_data["CE_buy"]=CE_stoploss_orderid

                test_data["PE_margin_sell"]=PE_sell_order
                test_data["CE_margin_sell"]=CE_sell_order

                print(test_data)
                
                break

            if(PE_stoploss_orderid!=None and CE_stoploss_orderid!=None):
                # logging.info("waiting till the exit time...")
                if(PE_margin): PE_sell_order=sell(tradingSym_PE_margin)
                if(CE_margin): CE_sell_order=sell(tradingSym_CE_margin)

                test_data["PE_buy"]=PE_stoploss_orderid
                test_data["CE_buy"]=CE_stoploss_orderid

                test_data["PE_margin_sell"]=PE_sell_order
                test_data["CE_margin_sell"]=CE_sell_order

                print(test_data)
                
                break

            else:
                print("checking for stoploss... time: {}".format(get_current_time()))
                
                PE_stoploss_status=stoploss_reached(PE_stoploss_orderid,cur_PE_price,limit_PE)
                CE_stoploss_status=stoploss_reached(CE_stoploss_orderid,cur_CE_price,limit_CE)

                print("PE_price: {} limit_PE: {}".format(cur_PE_price,limit_PE))
                print("CE_price: {} limit_CE: {}".format(cur_CE_price,limit_CE))

                if(PE_stoploss_status): PE_stoploss_orderid=place_order(tradingSym_PE,"buy",kite_exchange,kite.ORDER_TYPE_MARKET,kite.PRODUCT_MIS)
                if(CE_stoploss_status): CE_stoploss_orderid=place_order(tradingSym_CE,"buy",kite_exchange,kite.ORDER_TYPE_MARKET,kite.PRODUCT_MIS)
                         
            time.sleep(1)
                

        # Fetch all orders
        logging.info("kite orders {}".format(kite.orders()))
        
def main():
    place_order_time(entry_time_hour,entry_time_min)

if __name__=="__main__":
    main()