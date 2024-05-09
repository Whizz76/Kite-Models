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
logging.info("Executing testKite.py")

api_key = "t416qxyj6fek1upt"
kite = KiteConnect(api_key=api_key)

# access_token = "3UUeC4Z2VvtDykXT6RsbSpc7X7zjpkFc"
kite.set_access_token(access_token)

net = kite.margins()["equity"]["net"]
logging.info("net: {}".format(net))
stoploss=0.002

exchange1="NSE"
exchange2="NSE"
kite_exchange=kite.EXCHANGE_NSE
if(exchange2=="BFO"): kite_exchange=kite.EXCHANGE_BFO

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
    margin_percentage=0.7
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
    logging.info("placing {} sl-order current time {}".format(direction,datetime.now().time()))
    trigger_price=price
    
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
ratio_limit=0.999
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

        tradingSym_PE="DEVYANI"
        tradingSym_CE="DEVYANI"

        logging.info("PE_sym {}".format(tradingSym_PE))
        logging.info("CE_sym {}".format(tradingSym_CE))

        num_lots=1
        no_order=False


        if(num_lots!=0):
            
            quantity=1

            PE_LTP=None
            CE_LTP=None
            limit_PE=None
            limit_CE=None
            
            # Check if the sell order have been executed or not
            PE_ATM_sell_status=False
            CE_ATM_sell_status=False

           
            PE_ATM_sell_order=place_order(tradingSym_PE,"sell",kite_exchange,kite.ORDER_TYPE_MARKET,kite.PRODUCT_MIS,quantity,0)
            # PE_ATM_sell_order=True
            if(PE_ATM_sell_order): 
                time.sleep(1)
                PE_LTP=kite.quote(exchange2+":"+tradingSym_PE)[exchange2+":"+tradingSym_PE]['last_price']
                PE_ATM_sell_status=True
                limit_PE=PE_LTP*(1+stoploss)
                limit_PE=round(limit_PE,1)
                # limit_PE=min(limit_PE,170)
                logging.info("limit_PE: {}".format(limit_PE))
                PE_buy_id=place_sl_order(tradingSym_PE,"buy",kite_exchange,kite.ORDER_TYPE_SL,kite.PRODUCT_MIS,quantity,limit_PE)
        

            CE_ATM_sell_order=place_order(tradingSym_CE,"sell",kite_exchange,kite.ORDER_TYPE_MARKET,kite.PRODUCT_MIS,quantity,0)
            # CE_ATM_sell_order=True
            if(CE_ATM_sell_order): 
                time.sleep(1)
                CE_LTP=kite.quote(exchange2+":"+tradingSym_CE)[exchange2+":"+tradingSym_CE]['last_price']
                CE_ATM_sell_status=True
                limit_CE=CE_LTP*(1+stoploss)
                limit_CE=round(limit_CE,1)
                # limit_CE=min(limit_CE,170)
                logging.info("limit_CE: {}".format(limit_CE))
                CE_buy_id=place_sl_order(tradingSym_CE,"buy",kite_exchange,kite.ORDER_TYPE_SL,kite.PRODUCT_MIS,quantity,limit_CE)

            # A paramter ti check if the stoploss order has been executed or not
            PE_limit_buy_status=False
            CE_limit_buy_status=False
            
            while True:

                cur_PE_price=kite.quote(exchange2+":"+tradingSym_PE)[exchange2+":"+tradingSym_PE]['last_price']
                cur_CE_price=kite.quote(exchange2+":"+tradingSym_CE)[exchange2+":"+tradingSym_CE]['last_price']

                # If sell order could not be executed then no need to place the buy order
                if(PE_ATM_sell_status==False): PE_limit_buy_status=True
                if(CE_ATM_sell_status==False): CE_limit_buy_status=True

                limit_PE=min_val(cur_PE_price,stoploss,limit_PE)
                limit_CE=min_val(cur_CE_price,stoploss,limit_CE)
                limit_PE=round(limit_PE,1)
                limit_CE=round(limit_CE,1)


                logging.info("cur_PE_price: {} limit_PE: {}".format(cur_PE_price,limit_PE))
                logging.info("cur_CE_price: {} limit_CE: {}".format(cur_CE_price,limit_CE))


                if is_current_time(13,00):
                    logging.info("Exiting the program")
                    break

                else:
                    place_PE_limit_order=place_limit_order(cur_PE_price,PE_LTP)
                    place_CE_limit_order=place_limit_order(cur_CE_price,CE_LTP)
                    
                    if(place_PE_limit_order and PE_limit_buy_status==False): 
                        if(order_status(PE_buy_id,"OPEN")): 
                            cancelled_PE_id=kite.cancel_order(variety=kite.VARIETY_REGULAR,order_id=str(PE_buy_id))
                            if(order_status(PE_buy_id,"CANCELLED")):
                                logging.info("order cancelled {}".format(cancelled_PE_id))
                                PE_buy_id=place_sl_order(tradingSym_PE,"buy",kite_exchange,kite.ORDER_TYPE_SL,kite.PRODUCT_MIS,quantity,limit_PE)
                                PE_LTP=cur_PE_price
                            else: logging.info("order not cancelled")
                        else: PE_limit_buy_status=True

                    if(place_CE_limit_order and CE_limit_buy_status==False): 
                        if(order_status(CE_buy_id,"OPEN")): 
                            cancelled_CE_id=kite.cancel_order(variety=kite.VARIETY_REGULAR,order_id=str(CE_buy_id))
                            if(order_status(CE_buy_id,"CANCELLED")):
                                logging.info("order cancelled {}".format(cancelled_CE_id))
                                CE_buy_id=place_sl_order(tradingSym_CE,"buy",kite_exchange,kite.ORDER_TYPE_SL,kite.PRODUCT_MIS,quantity,limit_CE)
                                CE_LTP=cur_CE_price
                            else: logging.info("order not cancelled")
                        else: CE_limit_buy_status=True

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
                    
                    tradingSym_PE="DEVYANI"
                    tradingSym_CE="DEVYANI"

                    PE_ATM_sell_status=False
                    CE_ATM_sell_status=False

                    
                    
                    PE_ATM_sell_order=place_order(tradingSym_PE,"sell",kite_exchange,kite.ORDER_TYPE_MARKET,kite.PRODUCT_MIS,quantity,0)
                    if(PE_ATM_sell_order):
                        time.sleep(1)
                        PE_LTP=kite.quote(exchange2+":"+tradingSym_PE)[exchange2+":"+tradingSym_PE]['last_price']
                        PE_ATM_sell_status=True
                        limit_PE=PE_LTP*(1+stoploss)
                        limit_PE=round(limit_PE,1)
                        # limit_PE=min(limit_PE,170)
                        PE_limit_buy_status=False
                        PE_buy_id=place_sl_order(tradingSym_PE,"buy",kite_exchange,kite.ORDER_TYPE_SL,kite.PRODUCT_MIS,quantity,limit_PE)

                    CE_ATM_sell_order=place_order(tradingSym_CE,"sell",kite_exchange,kite.ORDER_TYPE_MARKET,kite.PRODUCT_MIS,quantity,0)
                    if(CE_ATM_sell_order):
                        time.sleep(1)
                        CE_LTP=kite.quote(exchange2+":"+tradingSym_CE)[exchange2+":"+tradingSym_CE]['last_price']
                        CE_ATM_sell_status=True
                        limit_CE=CE_LTP*(1+stoploss)
                        limit_CE=round(limit_CE,1)
                        # limit_CE=min(limit_CE,170)
                        CE_limit_buy_status=False
                        CE_buy_id=place_sl_order(tradingSym_CE,"buy",kite_exchange,kite.ORDER_TYPE_SL,kite.PRODUCT_MIS,quantity,limit_CE)
                    
                            
                time.sleep(1)
                    

        # Fetch all orders
        logging.info("kite orders {}".format(kite.orders()))
        
def main():
    place_order_time(9,00)

if __name__=="__main__":
    main()