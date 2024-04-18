import pandas as pd
from datetime import datetime, timedelta
import time as time
import json
import requests
import logging

# URL of the API endpoint
api_url = "http://localhost:5000/random_number"

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

# print(entry_time_hour,entry_time_min,exit_time_hour,exit_time_min)
# print(stoploss,trade_size,symbol,trading_symbol,margin_range)
# -----------------------------------------------------------------------
kite_exchange="kite.EXCHANGE_NFO"
if(exchange2=="BFO"): kite_exchange="kite.EXCHANGE_BFO"

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
print("symbol {}".format(symbol))

def is_current_time(hour, minute):
    # Get current time
    current_time = datetime.now().time()
    
    # Check if current hour and minute match the parameters
    return current_time.hour >= hour and current_time.minute >= minute

def get_price():
    # Make a GET request to the API endpoint
    response = requests.get(api_url)

    # Check if the request was successful (status code 200)
    if response.status_code == 200:
        # Extract the JSON data from the response
        data = response.json()
        # Extract the random number from the JSON data
        random_number = data['random_number']
        print("get_price {} cur_time {}".format(random_number,datetime.now() ))
        return random_number
    else:
        print("Error:", response.status_code)
        return None


# Place an order
def place_order(symbol,direction,exchange,o_type,product):
    
    try:
        res = requests.get(api_url)

        # Check if the request was successful (status code 200)
        if res.status_code == 200:
            # Extract the JSON data from the response
            d = res.json()
            # Extract the random number from the JSON data
            ran_num = d['random_number']
            print("price {} sym {} direction {} order time {}".format(ran_num,symbol,direction,datetime.now() ))
            return ran_num
        else:
            print("Error:", res.status_code)
    
    except Exception as e:
        print("Order placement failed: {}".format(e))
        return None

def stoploss_reached(stoposs_id,cur_price,LTP_limit):
    return stoposs_id==None and cur_price>=LTP_limit

def place_order_time(time_hour,time_minute):

    placeOrder=False

    while True:
        if is_current_time(time_hour,time_minute):
            placeOrder=True
            break
        else:
            print("Waiting for the right time to place order")
            time.sleep(1)

    if(placeOrder):

        token_ltp = get_price()
        SP=int(round(token_ltp,-2))
        print("SP: {}".format(SP))
        
        CE_price=SP
        PE_price=SP

        tradingSym_PE=symbol+str(PE_price)+"PE"
        tradingSym_CE=symbol+str(CE_price)+"CE"

        print("PE_sym {}".format(tradingSym_PE))
        print("CE_sym {}".format(tradingSym_CE))

        CE_price=SP+margin_range
        PE_price=SP-margin_range

        tradingSym_PE_margin=symbol+str(PE_price)+"PE"
        tradingSym_CE_margin=symbol+str(CE_price)+"CE"

        PE_margin=place_order(tradingSym_PE_margin,"buy",kite_exchange,"kite.ORDER_TYPE_MARKET","kite.PRODUCT_MIS")
        CE_margin=place_order(tradingSym_CE_margin,"buy",kite_exchange,"kite.ORDER_TYPE_MARKET","kite.PRODUCT_MIS")

        PE_LTP=None
        CE_LTP=None

        if(PE_margin and CE_margin): 
            PE_order=place_order(tradingSym_PE,"sell",kite_exchange,"kite.ORDER_TYPE_MARKET","kite.PRODUCT_MIS")
            time.sleep(1)
            if(PE_order): PE_LTP=get_price()

            CE_order=place_order(tradingSym_CE,"sell",kite_exchange,"kite.ORDER_TYPE_MARKET","kite.PRODUCT_MIS")
            time.sleep(1)
            if(CE_order): CE_LTP=get_price()
        
        PE_CE_LTP=min(PE_LTP,CE_LTP)
        limit_PE=PE_LTP+(PE_CE_LTP*stoploss)
        limit_CE=CE_LTP+(PE_CE_LTP*stoploss)

        PE_stoploss_orderid=None
        CE_stoploss_orderid=None

        while True:

            cur_PE_price=get_price()
            cur_CE_price=get_price()


            if is_current_time(exit_time_hour,exit_time_min):

                if(PE_stoploss_orderid==None): PE_stoploss_orderid=place_order(tradingSym_PE,"buy",kite_exchange,"kite.ORDER_TYPE_MARKET","kite.PRODUCT_MIS")
                if(CE_stoploss_orderid==None): CE_stoploss_orderid=place_order(tradingSym_CE,"buy",kite_exchange,"kite.ORDER_TYPE_MARKET","kite.PRODUCT_MIS")

                if(PE_margin): PE_sell_order=place_order(tradingSym_PE_margin,"sell",kite_exchange,"kite.ORDER_TYPE_MARKET","kite.PRODUCT_MIS")
                if(CE_margin): CE_sell_order=place_order(tradingSym_CE_margin,"sell",kite_exchange,"kite.ORDER_TYPE_MARKET","kite.PRODUCT_MIS")
                
                break

            elif(PE_stoploss_orderid!=None and CE_stoploss_orderid!=None):
                print("waiting till the exit time cur_time {}...".format(datetime.now() ))
                continue

            else:
                
                PE_stoploss_status=stoploss_reached(PE_stoploss_orderid,cur_PE_price,limit_PE)
                CE_stoploss_status=stoploss_reached(CE_stoploss_orderid,cur_CE_price,limit_CE)

                if (PE_stoploss_status):
                    print("waiting for 50sec for Put option, cur_time {}...".format(datetime.now()))
                    time.sleep(50)

                    cur_PE_price=get_price()
                    PE_stoploss_status=stoploss_reached(PE_stoploss_orderid,cur_PE_price,limit_PE)

                    if(PE_stoploss_status): PE_stoploss_orderid=place_order(tradingSym_PE,"buy",kite_exchange,"kite.ORDER_TYPE_MARKET","kite.PRODUCT_MIS")

                if(CE_stoploss_status):
                    print("waiting for 50sec for Call option, curr_time {}...".format(datetime.now()))
                    time.sleep(50)

                    cur_CE_price=get_price()
                    CE_stoploss_status=stoploss_reached(CE_stoploss_orderid,cur_CE_price,limit_CE)

                    if(CE_stoploss_status): CE_stoploss_orderid=place_order(tradingSym_CE,"buy",kite_exchange,"kite.ORDER_TYPE_MARKET","kite.PRODUCT_MIS")
            print("stoploss not reached yet cur_time {}...".format(datetime.now() ))       
            time.sleep(1)
                

        # Fetch all orders
        # print("kite orders {}".format(kite.orders()))
        
def main():
    place_order_time(entry_time_hour,entry_time_min)

if __name__=="__main__":
    main()