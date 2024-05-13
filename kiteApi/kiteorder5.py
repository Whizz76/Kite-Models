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
logging.info("Executing kiteorder3.py")

api_key = "t416qxyj6fek1upt"
kite = KiteConnect(api_key=api_key)

# get the request token from "https://kite.trade/connect/login?api_key=xxxxx&v=3" and login.
# data = kite.generate_session("h3PyhDEbw3N5yO7X9WNclOcPpKa6tSjD",api_secret="oc4jdd5sa8k6e7m6r463s898blepehmj")
# logging.info(data)

# Get the access token from the above response and store it in a variable
access_token = "dxfHFTxKSKTGgTro49yv5fSX5ddNfqjI"
kite.set_access_token(access_token)

net = kite.margins()["equity"]["net"]
logging.info("net: {}".format(net))

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
lot_size=int(input_values["quantity"])

symbol=str(input_values["instrument_token"]).upper()
sym=str(input_values["trading_symbol"]).upper()

is_last_week=int(input_values["last_week"])
nearest_range=int(input_values["nearest_range"])

exchange1=str(input_values["exchange"]).upper()
exchange2="NFO"
if(exchange1=="BSE"): exchange2="BFO"

margin_range=int(input_values["margin_range"])

# logging.info(entry_time_hour,entry_time_min,exit_time_hour,exit_time_min)
# logging.info(stoploss,lot_size,symbol,trading_symbol,margin_range)
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

result_string = ""

if is_last_week:
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
    # (start the process if the current time is greater than or equal to the given time)
    return current_time.hour >= hour and current_time.minute >= minute

# check find the number of lots that can be traded 

def num_lots_fun(sell_sym,buy_sym,lot_size,exchange2):
    # Fetch margin detail for order/orders
    num_lots=0
    margin_percentage=0.3
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
                "quantity": lot_size
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
                "quantity": lot_size
            }
        )
    try:
        # Fetch margin detail for single order
        margin_net_available = kite.margins()["equity"]["net"]

        # Using a percentage of the available margin
        margin_net_available=margin_net_available*margin_percentage

        margin_detail = kite.basket_order_margins(order_param_basket)
        margin_required = margin_detail["final"]["total"]

        # Calculate the number of lots that can be traded
        num_lots=int(margin_net_available/margin_required)
        logging.info("Available margin: {} , Required margin: {}".format(margin_net_available,margin_required))   

    except Exception as e:
        logging.info("Error fetching order margin: {}".format(e))

    logging.info("num_lots: {}".format(num_lots))
    return num_lots

# Get the strike price for a given token

def get_strike_price(token,range):
    ltp=kite.quote(token)[token]['last_price']
    logging.info("actual ltp: {}".format(ltp))

    ltp_rounded_2=int(round(ltp,-2))
    if(range==100): return ltp_rounded_2

    ltp_rounded_1=int(round(ltp,-1))    
    temp=ltp_rounded_1

    if(ltp_rounded_1>ltp_rounded_2): ltp_rounded_1=ltp_rounded_2+50
    else: ltp_rounded_1=ltp_rounded_2-50

    if(abs(temp-ltp_rounded_1)>abs(temp-ltp_rounded_2)): return ltp_rounded_2
    else: return ltp_rounded_1



# Check if the order was successful
def order_status(order_id,status):
    for order in kite.orders():
        if order["order_id"] == str(order_id):
            if(status=="OPEN"): return order["status"] == "OPEN" or order["status"] == "TRIGGER PENDING"
            return order["status"] == status
    return False

# Place an order
def place_order(symbol,direction,exchange,o_type,product,quantity,price):
    logging.info("placing {} order current time {}".format(direction,datetime.now().time()))
    
    try:
        order_id = kite.place_order(tradingsymbol=symbol,
                                    exchange=exchange,
                                    transaction_type=kite.TRANSACTION_TYPE_BUY if direction == "buy" else kite.TRANSACTION_TYPE_SELL,
                                    quantity=quantity,
                                    variety=kite.VARIETY_REGULAR,
                                    order_type=o_type,
                                    product=product)
        
        # If the order was successful return the order id
        if(order_status(order_id,"COMPLETE")): 
            logging.info("Order placed. ID is: {}".format(order_id))
            return order_id
        
        else:
            logging.info("Error {}".format(order_id))
            return None
        
    except Exception as e:
        logging.info("Order placement failed: {}".format(e))
        return None

# placing a SL-Limit order
def place_sl_order(symbol,direction,exchange,o_type,product,quantity,price):
    price=round(price,1)
    logging.info("placing {} sl-order current time {}".format(direction,datetime.now().time()))
    trigger_price=price*0.9875
    trigger_price=round(trigger_price,1)
    logging.info("trigger_price: {} limit_price {}".format(trigger_price,price))
    
    try:
        order_id = kite.place_order(tradingsymbol=symbol,
                                    exchange=exchange,
                                    transaction_type=kite.TRANSACTION_TYPE_BUY if direction == "buy" else kite.TRANSACTION_TYPE_SELL,
                                    quantity=quantity,
                                    variety=kite.VARIETY_REGULAR,
                                    order_type=o_type,
                                    product=product,
                                    price=price,
                                    trigger_price=trigger_price)
        
        # If the order was successful return the order id
        if(order_status(order_id,"OPEN") or order_status(order_id,"COMPLETE")): 
            logging.info("Order placed. ID is: {}".format(order_id))
            return order_id
        
        else:
            logging.info("Error {}".format(order_id))
            return None
        
    except Exception as e:
        logging.info("Order placement failed: {}".format(e))
        return None

# Check if the stoploss has been reached
ratio_limit=0.9
def place_limit_order(cur_price,previous_price):
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

        token_ltp = get_strike_price(temp,nearest_range)
        SP=int(token_ltp)
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
        num_lots=num_lots_fun(sell_sym,buy_sym,lot_size,exchange2)
        # Delete it later
        if(num_lots==0 or num_lots>1): num_lots=1
        logging.info("num_lots for order: {}".format(num_lots))
        no_order=False


        if(num_lots!=0):
            quantity=lot_size*num_lots

            PE_OTM_buy_order=place_order(tradingSym_PE_margin,"buy",kite_exchange,kite.ORDER_TYPE_MARKET,kite.PRODUCT_MIS,quantity,0)
            CE_OTM_buy_order=place_order(tradingSym_CE_margin,"buy",kite_exchange,kite.ORDER_TYPE_MARKET,kite.PRODUCT_MIS,quantity,0)

            PE_LTP=None
            CE_LTP=None
            limit_PE=None
            limit_CE=None
            
            # Check if the sell order have been executed or not
            PE_ATM_sell_status=False
            CE_ATM_sell_status=False

            if(PE_OTM_buy_order and CE_OTM_buy_order): 
                PE_ATM_sell_order=place_order(tradingSym_PE,"sell",kite_exchange,kite.ORDER_TYPE_MARKET,kite.PRODUCT_MIS,quantity,0)
                if(PE_ATM_sell_order): 
                    time.sleep(1)
                    PE_LTP=kite.quote(exchange2+":"+tradingSym_PE)[exchange2+":"+tradingSym_PE]['last_price']
                    PE_ATM_sell_status=True
                    limit_PE=PE_LTP*(1+stoploss)
                    limit_PE=round(limit_PE,1)
                    PE_buy_id=place_sl_order(tradingSym_PE,"buy",kite_exchange,kite.ORDER_TYPE_SL,kite.PRODUCT_MIS,quantity,limit_PE)
            

                CE_ATM_sell_order=place_order(tradingSym_CE,"sell",kite_exchange,kite.ORDER_TYPE_MARKET,kite.PRODUCT_MIS,quantity,0)
                if(CE_ATM_sell_order): 
                    time.sleep(1)
                    CE_LTP=kite.quote(exchange2+":"+tradingSym_CE)[exchange2+":"+tradingSym_CE]['last_price']
                    CE_ATM_sell_status=True
                    limit_CE=CE_LTP*(1+stoploss)
                    limit_CE=round(limit_CE,1)
                    CE_buy_id=place_sl_order(tradingSym_CE,"buy",kite_exchange,kite.ORDER_TYPE_SL,kite.PRODUCT_MIS,quantity,limit_CE)
    
            # A paramter ti check if the stoploss order has been executed or not
            PE_limit_buy_status=False
            CE_limit_buy_status=False
            
            while True:

                cur_PE_price=kite.quote(exchange2+":"+tradingSym_PE)[exchange2+":"+tradingSym_PE]['last_price']
                cur_CE_price=kite.quote(exchange2+":"+tradingSym_CE)[exchange2+":"+tradingSym_CE]['last_price']

                # If sell order could not be executed or SL is hit then no need to place the buy order
                if(PE_limit_buy_status==False):
                    if(PE_ATM_sell_status==False or order_status(PE_buy_id,"COMPLETE")): PE_limit_buy_status=True
                
                if(CE_limit_buy_status==False):
                    if(CE_ATM_sell_status==False or order_status(CE_buy_id,"COMPLETE")): CE_limit_buy_status=True

                limit_PE=min_val(cur_PE_price,stoploss,limit_PE)
                limit_CE=min_val(cur_CE_price,stoploss,limit_CE)
                limit_PE=round(limit_PE,1)
                limit_CE=round(limit_CE,1)

                logging.info("cur_PE_price: {} limit_PE: {}".format(cur_PE_price,limit_PE))
                logging.info("cur_CE_price: {} limit_CE: {}".format(cur_CE_price,limit_CE))


                if is_current_time(exit_time_hour,exit_time_min):
                    logging.info("Exiting the program")
                    if(PE_OTM_buy_order): PE_OTM_sell_order=place_order(tradingSym_PE_margin,"sell",kite_exchange,kite.ORDER_TYPE_MARKET,kite.PRODUCT_MIS,quantity,0)
                    if(CE_OTM_buy_order): CE_OTM_sell_order=place_order(tradingSym_CE_margin,"sell",kite_exchange,kite.ORDER_TYPE_MARKET,kite.PRODUCT_MIS,quantity,0)
                    
                    break

                else:
                    place_PE_limit_order=place_limit_order(cur_PE_price,PE_LTP)
                    place_CE_limit_order=place_limit_order(cur_CE_price,CE_LTP)
                    
                    if(place_PE_limit_order and PE_limit_buy_status==False): 
                        if(PE_buy_id and order_status(PE_buy_id,"OPEN")): 
                            temp_id=PE_buy_id
                            PE_buy_id=place_sl_order(tradingSym_PE,"buy",kite_exchange,kite.ORDER_TYPE_SL,kite.PRODUCT_MIS,quantity,limit_PE)
                            PE_LTP=cur_PE_price
                            cancelled_PE_id=kite.cancel_order(variety=kite.VARIETY_REGULAR,order_id=str(temp_id))
                            # time.sleep(1)
                            # if(order_status(PE_buy_id,"CANCELLED")):
                            logging.info("order cancelled {} temp_id {}".format(cancelled_PE_id,temp_id))
                            
                            # else: logging.info("order not cancelled")

                        elif(PE_buy_id==None): 
                            PE_buy_id=place_sl_order(tradingSym_PE,"buy",kite_exchange,kite.ORDER_TYPE_SL,kite.PRODUCT_MIS,quantity,limit_PE)
                            PE_LTP=cur_PE_price

                        else: PE_limit_buy_status=True

                    if(place_CE_limit_order and CE_limit_buy_status==False): 
                        if(CE_buy_id and order_status(CE_buy_id,"OPEN")):
                            temp_id=CE_buy_id 
                            CE_buy_id=place_sl_order(tradingSym_CE,"buy",kite_exchange,kite.ORDER_TYPE_SL,kite.PRODUCT_MIS,quantity,limit_CE)
                            CE_LTP=cur_CE_price
                            cancelled_CE_id=kite.cancel_order(variety=kite.VARIETY_REGULAR,order_id=str(temp_id))
                            # time.sleep(1)
                            # if(order_status(CE_buy_id,"CANCELLED")):
                            logging.info("order cancelled {} temp_id {}".format(cancelled_CE_id,temp_id))
                            # else: logging.info("order not cancelled")

                        elif(CE_buy_id==None):
                            CE_buy_id=place_sl_order(tradingSym_CE,"buy",kite_exchange,kite.ORDER_TYPE_SL,kite.PRODUCT_MIS,quantity,limit_CE)
                            CE_LTP=cur_CE_price

                        else: CE_limit_buy_status=True

                if(PE_limit_buy_status and CE_limit_buy_status):
                    if(no_order): 
                        logging.info("no order possible")
                        continue

                    # globals()["total_orders"]=globals()["total_orders"]+1
                    total_orders=total_orders+1
                    logging.info("total_orders: {}".format(total_orders))

                    if(total_orders>1 or is_current_time(13,00)): 
                        logging.info("total orders exceeded or the time is 1:00 pm")
                        no_order=True
                        continue

                    logging.info("limit buy orders completed, again placing the sell orders....")

                    token_ltp = get_strike_price(temp,nearest_range)
                    SP=int(token_ltp)
                    logging.info("SP: {}".format(SP))
                    tradingSym_PE=symbol+str(SP)+"PE"
                    tradingSym_CE=symbol+str(SP)+"CE"

                    sell_sym=[tradingSym_PE,tradingSym_CE]
                    buy_sym=[]
                    new_num_lots=num_lots_fun(sell_sym,buy_sym,lot_size,exchange2)

                    if(new_num_lots<num_lots): 
                        quantity=new_num_lots*lot_size

                    PE_ATM_sell_status=False
                    CE_ATM_sell_status=False

                    PE_ATM_sell_order=place_order(tradingSym_PE,"sell",kite_exchange,kite.ORDER_TYPE_MARKET,kite.PRODUCT_MIS,quantity,0)
                    if(PE_ATM_sell_order):
                        time.sleep(1)
                        PE_LTP=kite.quote(exchange2+":"+tradingSym_PE)[exchange2+":"+tradingSym_PE]['last_price']
                        PE_ATM_sell_status=True
                        limit_PE=PE_LTP*(1+stoploss)
                        PE_limit_buy_status=False
                        limit_PE=round(limit_PE,1)
                        PE_buy_id=place_sl_order(tradingSym_PE,"buy",kite_exchange,kite.ORDER_TYPE_SL,kite.PRODUCT_MIS,quantity,limit_PE)

                    CE_ATM_sell_order=place_order(tradingSym_CE,"sell",kite_exchange,kite.ORDER_TYPE_MARKET,kite.PRODUCT_MIS,quantity,0)
                    if(CE_ATM_sell_order):
                        time.sleep(1)
                        CE_LTP=kite.quote(exchange2+":"+tradingSym_CE)[exchange2+":"+tradingSym_CE]['last_price']
                        CE_ATM_sell_status=True
                        limit_CE=CE_LTP*(1+stoploss)
                        limit_CE=round(limit_CE,1)
                        CE_limit_buy_status=False
                        CE_buy_id=place_sl_order(tradingSym_CE,"buy",kite_exchange,kite.ORDER_TYPE_SL,kite.PRODUCT_MIS,quantity,limit_CE)
                    
                            
                time.sleep(1)
                    

        # Fetch all orders
        logging.info("kite orders {}".format(kite.orders()))
        
def main():
    place_order_time(entry_time_hour,entry_time_min)

if __name__=="__main__":
    main()