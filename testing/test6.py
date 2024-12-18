import logging
from kiteconnect import KiteConnect
import kiteconnect.exceptions
from kiteconnect import KiteTicker
import pandas as pd
import datetime
import time
import json
import requests

logging.basicConfig(level=logging.DEBUG)
logging.info("Executing test6.py")

print("started...")
api_key = "t416qxyj6fek1upt"
kite = KiteConnect(api_key=api_key)
test_data={}
folder_path="BNF"
token="BANKNIFTY"
tokenSymbol="NIFTY BANK24416"
# get the request token from "https://kite.trade/connect/login?api_key=xxxxx&v=3" and login.
# data = kite.generate_session("h3PyhDEbw3N5yO7X9WNclOcPpKa6tSjD",api_secret="oc4jdd5sa8k6e7m6r463s898blepehmj")
# logging.info(data)

# Initializing the input parameters
# -----------------------------------------------------------------------

input_df=pd.read_csv("input.csv")

expiry_date="2024-04-16"
test_date="2024-04-16"
test_weekday=2

entry_time_hour=9
entry_time_min=35
entry_time_sec=0

exit_time_hour=15
exit_time_min=15

input_values=input_df.loc[test_weekday]

entry_time_hour=int(input_values["entry_time"][0:2])
entry_time_min=int(input_values["entry_time"][-2:])

exit_time_hour=int(input_values["exit_time"][0:2])
exit_time_min=int(input_values["exit_time"][-2:])

stoploss=float(input_values["stoploss"])
trade_size=int(input_values["quantity"])

symbol=str(input_values["instrument_token"]).upper()
sym=str(input_values["trading_symbol"]).upper()

is_last_week=int(input_values["last_week"])
nearest_range=int(input_values["nearest_range"])

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
current_date = datetime.datetime.strptime(test_date, "%Y-%m-%d")
# Extract year's last two digits
year_last_two_digits = str(current_date.year)[-2:]

# Extract month index
month_index = str(current_date.month)
# Extract day
day = str(current_date.day) 

result_string = ""

if is_last_week:
    # If yes, add the first three letters of the current month
    result_string=year_last_two_digits+ "APR"

else:

    if current_date.month<10:
        result_string = year_last_two_digits + month_index.zfill(1) + day.zfill(2)
    # Form the string in the format yymdd
    else: result_string = year_last_two_digits + month_index.zfill(2) + day.zfill(2)


symbol=sym+result_string
logging.info("symbol {}".format(symbol))

cur_time=datetime.time(9,35,0)

def update_time():
    # Update time by 1 second
    globals()["cur_time"] = (datetime.datetime.combine(datetime.date(1, 1, 1), globals()["cur_time"]) + datetime.timedelta(seconds=1)).time()
    logging.info("Time updated to: {}".format(globals()["cur_time"]))

def is_current_time(hour, minute):
    # Get current time
    current_time = globals()["cur_time"]
    # Check if current hour and minute match the parameters
    return current_time.hour >= hour and current_time.minute >= minute

# Get the ltp
def get_ltp(trading_symbol):
    print("trading symbol: {}".format(trading_symbol))
    BNF_file=pd.read_csv("./"+folder_path+"/"+expiry_date+"/"+trading_symbol+".csv")
    current_time=globals()["cur_time"].strftime("%H:%M:%S")
    BNF_file=BNF_file[BNF_file["timestamp"]==test_date+" "+current_time]
    if(not BNF_file.empty): 
        BNF_file=BNF_file.values[0]
        return float(BNF_file[2])
    else: return 10000
    
def place_order(tradingSym,transaction_type,exchange,order_type,product,quantity,price):
    BNF_file=pd.read_csv("./"+folder_path+"/"+expiry_date+"/"+tradingSym+".csv")
    current_time=globals()["cur_time"].strftime("%H:%M:%S")
    BNF_file=BNF_file[BNF_file["timestamp"]==test_date+" "+current_time]
    if(not BNF_file.empty):
        BNF_file=BNF_file.values[0]
        print(BNF_file[0])
        logging.info("direction: {} price {} symbol {} time {}".format(transaction_type,BNF_file[2],tradingSym,current_time))
        return float(BNF_file[2])
    else: return None

def sell(tradingSym):
    BNF_file=pd.read_csv("./"+folder_path+"/"+expiry_date+"/"+tradingSym+".csv")
    sell_LTP=BNF_file[BNF_file["timestamp"].str.contains(test_date+" "+"15:18")].iloc[0]
    print("sell order {} price {}".format(tradingSym,sell_LTP["ltp"]))
    return float(sell_LTP["ltp"])

# Check if the stoploss has been reached
ratio_limit=0.9
def place_limit_order(cur_price,previous_price):
    if(cur_price==None or previous_price==None): return False
    logging.info("cur_price: {} previous_price: {}".format(cur_price,previous_price))
    ratio=float(cur_price/previous_price)
    logging.info("ratio: {}".format(ratio))
    return ratio<=ratio_limit


# Get the minimum LTP_stoploss_limit
def min_val(cur_price,stoploss,min_ltp):
    lim_ltp=cur_price*(1+stoploss)
    if(min_ltp==None): return lim_ltp

    if(lim_ltp<min_ltp): 
        min_ltp=lim_ltp
    return min_ltp

def get_strike_price(token,range):
    ltp=get_ltp(token)
    logging.info("actual ltp: {}".format(ltp))

    ltp_rounded_2=int(round(ltp,-2))
    if(range==100): return ltp_rounded_2

    ltp_rounded_1=int(round(ltp,-1))    
    temp=ltp_rounded_1

    if(ltp_rounded_1>ltp_rounded_2): ltp_rounded_1=ltp_rounded_2+50
    else: ltp_rounded_1=ltp_rounded_2-50

    if(abs(temp-ltp_rounded_1)>abs(temp-ltp_rounded_2)): return ltp_rounded_2
    else: return ltp_rounded_1

def is_triggered(price,cur_price):
    if(cur_price>=10000): return False
    trigger_price=price*0.9875
    trigger_price=round(trigger_price,1)
    if(cur_price>=trigger_price): logging.info("Price triggered with trigger_price {} cur_price {}".format(trigger_price,cur_price))
    return cur_price>=trigger_price

def place_order_time(time_hour,time_minute):

    total_orders=0
    placeOrder=False

    while True:
        if is_current_time(time_hour,time_minute):
            placeOrder=True
            break
        else:
            logging.info("Waiting for the right time to place order")
            time.sleep(1)

    if(placeOrder):

        SP=get_strike_price(tokenSymbol,nearest_range)
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

        num_lots=1
        no_order=False

        if(num_lots!=0):
            quantity=trade_size*num_lots

            PE_OTM_buy_order=place_order(tradingSym_PE_margin,"buy",kite_exchange,kite.ORDER_TYPE_MARKET,kite.PRODUCT_MIS,quantity,0)
            CE_OTM_buy_order=place_order(tradingSym_CE_margin,"buy",kite_exchange,kite.ORDER_TYPE_MARKET,kite.PRODUCT_MIS,quantity,0)
            test_data[str(tradingSym_PE_margin)]=-(get_ltp(tradingSym_PE_margin))
            test_data[str(tradingSym_CE_margin)]=-(get_ltp(tradingSym_CE_margin))

            PE_LTP=None
            CE_LTP=None
            limit_PE=None
            limit_CE=None
            PE_price=10000
            CE_price=10000
            
            # Check if the sell order have been executed or not
            PE_ATM_sell_status=False
            CE_ATM_sell_status=False

            if(PE_OTM_buy_order and CE_OTM_buy_order): 
                PE_ATM_sell_order=place_order(tradingSym_PE,"sell",kite_exchange,kite.ORDER_TYPE_MARKET,kite.PRODUCT_MIS,quantity,0)
                if(PE_ATM_sell_order): 
                    PE_LTP=get_ltp(tradingSym_PE)
                    PE_ATM_sell_status=True
                    limit_PE=PE_LTP*(1+stoploss)
                    limit_PE=round(limit_PE,1)
                    test_data[str(tradingSym_PE)]=PE_LTP
                    PE_price=limit_PE
                    PE_buy_id=place_order(tradingSym_PE,"buy",kite_exchange,kite.ORDER_TYPE_SL,kite.PRODUCT_MIS,quantity,limit_PE)
            

                CE_ATM_sell_order=place_order(tradingSym_CE,"sell",kite_exchange,kite.ORDER_TYPE_MARKET,kite.PRODUCT_MIS,quantity,0)
                if(CE_ATM_sell_order): 
                    CE_LTP=get_ltp(tradingSym_CE)
                    CE_ATM_sell_status=True
                    limit_CE=CE_LTP*(1+stoploss)
                    limit_CE=round(limit_CE,1)
                    test_data[str(tradingSym_CE)]=CE_LTP
                    CE_price=limit_CE
                    CE_buy_id=place_order(tradingSym_CE,"buy",kite_exchange,kite.ORDER_TYPE_SL,kite.PRODUCT_MIS,quantity,limit_CE)
    
            # A paramter ti check if the stoploss order has been executed or not
            PE_limit_buy_status=False
            CE_limit_buy_status=False

            PE_after_trigger=False
            CE_after_trigger=False
            PE_triggered=False
            CE_triggered=False
            
            while True:

                cur_PE_price=get_ltp(tradingSym_PE)
                cur_CE_price=get_ltp(tradingSym_CE)

                # If sell order could not be executed or SL is hit then no need to place the buy order
                if(PE_limit_buy_status==False):
                    if(PE_ATM_sell_status==False or PE_after_trigger): PE_limit_buy_status=True
                
                if(CE_limit_buy_status==False):
                    if(CE_ATM_sell_status==False or CE_after_trigger): CE_limit_buy_status=True

                limit_PE=min_val(cur_PE_price,stoploss,limit_PE)
                limit_CE=min_val(cur_CE_price,stoploss,limit_CE)
                limit_PE=round(limit_PE,1)
                limit_CE=round(limit_CE,1)

                logging.info("cur_PE_price: {} limit_PE: {}".format(cur_PE_price,limit_PE))
                logging.info("cur_CE_price: {} limit_CE: {}".format(cur_CE_price,limit_CE))

                if(PE_after_trigger==False):
                    if(PE_triggered and cur_PE_price<=PE_price):
                        PE_after_trigger=True
                        test_data[str(tradingSym_PE)]-=cur_PE_price
                        logging.info("Price triggered for {} limit_price {} cur_price {}".format(tradingSym_PE,PE_price,cur_PE_price))
                
                if(CE_after_trigger==False):
                    if(CE_triggered and cur_CE_price<=CE_price):
                        CE_after_trigger=True
                        test_data[str(tradingSym_CE)]-=cur_CE_price
                        logging.info("Price triggered for {} limit_price {} cur_price {}".format(tradingSym_CE,CE_price,cur_CE_price))
                        

                if(PE_triggered==False): PE_triggered=is_triggered(PE_price,cur_PE_price)
                if(CE_triggered==False): CE_triggered=is_triggered(CE_price,cur_CE_price)
                    

                if is_current_time(exit_time_hour,exit_time_min) or ((PE_limit_buy_status and CE_limit_buy_status) and total_orders>2):
                    logging.info("Exiting the program")
                    if(PE_OTM_buy_order): 
                        PE_OTM_sell_order=sell(tradingSym_PE_margin)
                        if(PE_OTM_sell_order): test_data[str(tradingSym_PE_margin)]+=get_ltp(tradingSym_PE_margin)

                    if(CE_OTM_buy_order): 
                        CE_OTM_sell_order=sell(tradingSym_CE_margin)
                        if(CE_OTM_sell_order): test_data[str(tradingSym_CE_margin)]+=get_ltp(tradingSym_CE_margin)
                    
                    break

                else:
                    place_PE_limit_order=place_limit_order(cur_PE_price,PE_LTP)
                    place_CE_limit_order=place_limit_order(cur_CE_price,CE_LTP)
                    
                    if(place_PE_limit_order and PE_limit_buy_status==False): 
                        if(PE_after_trigger): PE_limit_buy_status=True
                        
                        elif(PE_buy_id and PE_triggered==False): 
                            temp_id=PE_buy_id
                            PE_buy_id=place_order(tradingSym_PE,"buy",kite_exchange,kite.ORDER_TYPE_SL,kite.PRODUCT_MIS,quantity,limit_PE)
                            PE_LTP=cur_PE_price
                            PE_price=limit_PE
                            logging.info("order cancelled temp_id {}".format(temp_id))

                        elif(PE_buy_id==None): 
                            PE_buy_id=place_order(tradingSym_PE,"buy",kite_exchange,kite.ORDER_TYPE_SL,kite.PRODUCT_MIS,quantity,limit_PE)
                            PE_LTP=cur_PE_price
                            PE_price=limit_PE

                    if(place_CE_limit_order and CE_limit_buy_status==False): 
                        if(CE_after_trigger): CE_limit_buy_status=True

                        elif(CE_buy_id and CE_triggered==False):
                            temp_id=CE_buy_id 
                            CE_buy_id=place_order(tradingSym_CE,"buy",kite_exchange,kite.ORDER_TYPE_SL,kite.PRODUCT_MIS,quantity,limit_CE)
                            CE_LTP=cur_CE_price
                            logging.info("order cancelled temp_id {}".format(temp_id))
                            CE_price=limit_CE

                        elif(CE_buy_id==None):
                            CE_buy_id=place_order(tradingSym_CE,"buy",kite_exchange,kite.ORDER_TYPE_SL,kite.PRODUCT_MIS,quantity,limit_CE)
                            CE_LTP=cur_CE_price
                            CE_price=limit_CE

                if(PE_limit_buy_status and CE_limit_buy_status):
                    if(no_order): 
                        logging.info("no order possible")
                        continue

                    total_orders=total_orders+1
                    logging.info("total_orders: {}".format(total_orders))

                    if(total_orders>2 or is_current_time(13,00)): 
                        logging.info("total orders exceeded or the time is 1:00 pm")
                        no_order=True
                        continue

                    logging.info("limit buy orders completed, again placing the sell orders....")

                    token_ltp = get_strike_price(tokenSymbol,nearest_range)
                    SP=int(token_ltp)
                    if(SP==10000): 
                        logging.info("Strike price not found.. 404")
                        continue
                    logging.info("SP: {}".format(SP))
                    tradingSym_PE=symbol+str(SP)+"PE"
                    tradingSym_CE=symbol+str(SP)+"CE"

                    PE_ATM_sell_status=False
                    CE_ATM_sell_status=False

                    PE_ATM_sell_order=place_order(tradingSym_PE,"sell",kite_exchange,kite.ORDER_TYPE_MARKET,kite.PRODUCT_MIS,quantity,0)
                    if(PE_ATM_sell_order):
                        PE_LTP=get_ltp(tradingSym_PE)
                        PE_ATM_sell_status=True
                        limit_PE=PE_LTP*(1+stoploss)
                        PE_limit_buy_status=False
                        limit_PE=round(limit_PE,1)
                        PE_price=limit_PE
                        test_data[str(tradingSym_PE)]=PE_LTP
                        PE_buy_id=place_order(tradingSym_PE,"buy",kite_exchange,kite.ORDER_TYPE_SL,kite.PRODUCT_MIS,quantity,limit_PE)
                        PE_after_trigger=False
                        PE_triggered=False

                    CE_ATM_sell_order=place_order(tradingSym_CE,"sell",kite_exchange,kite.ORDER_TYPE_MARKET,kite.PRODUCT_MIS,quantity,0)
                    if(CE_ATM_sell_order):
                        CE_LTP=get_ltp(tradingSym_CE)
                        CE_ATM_sell_status=True
                        limit_CE=CE_LTP*(1+stoploss)
                        limit_CE=round(limit_CE,1)
                        CE_limit_buy_status=False
                        CE_price=limit_CE
                        test_data[str(tradingSym_CE)]=CE_LTP
                        CE_buy_id=place_order(tradingSym_CE,"buy",kite_exchange,kite.ORDER_TYPE_SL,kite.PRODUCT_MIS,quantity,limit_CE)
                        CE_triggered=False
                        CE_after_trigger=False

                            
                update_time()
                    

        # Fetch all orders
        logging.info("kite orders {}".format(test_data))
        
def main():
    place_order_time(entry_time_hour,entry_time_min)

if __name__=="__main__":
    main()