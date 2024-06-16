import logging
from kiteconnect import KiteConnect
import kiteconnect.exceptions
from kiteconnect import KiteTicker
import pandas as pd
from datetime import datetime, timedelta
import time as time
import json
import requests
from sys import exit

logging.basicConfig(level=logging.DEBUG)
logging.info("Executing kiteorder7C.py")

api_key = "t416qxyj6fek1upt"
kite = KiteConnect(api_key=api_key)

# Get the access token from the above response and store it in a variable
access_token = "tTdSMJUsOEO84IR1YRS0IRDDBWs4VQSq"
kite.set_access_token(access_token)
kws=KiteTicker(api_key,access_token)

net = kite.margins()["equity"]["net"]
logging.info("net: {}".format(net))

instruments = kite.instruments()
instruments=pd.json_normalize(instruments)
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
token_sym=symbol
sym=str(input_values["trading_symbol"]).upper()

is_last_week=int(input_values["last_week"])
nearest_range=int(input_values["nearest_range"])

exchange1=str(input_values["exchange"]).upper()
exchange2="NFO"
if(exchange1=="BSE"): exchange2="BFO"

margin_range=int(input_values["margin_range"])

kite_exchange=kite.EXCHANGE_NFO
if(exchange2=="BFO"): kite_exchange=kite.EXCHANGE_BFO

temp=exchange1+":"+symbol

# Getting the trading symbol

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
    result_string = year_last_two_digits + month_index + day.zfill(2)


symbol=sym+result_string

instruments = kite.instruments()
instruments=pd.json_normalize(instruments)

instrument_syms={}

for i in range(len(instruments)):
    if(symbol in instruments.loc[i,'tradingsymbol'] or instruments.loc[i,'tradingsymbol']==token_sym):
        instrument_syms[instruments.loc[i,'tradingsymbol']]=int(instruments.loc[i,'instrument_token'])

inst_ts=list(instrument_syms.values())

logging.info("symbol {}".format(symbol))
# Variable to check how many orders were requested
num_order_req=0


def is_current_time(hour, minute):
    # Get current time
    current_time = datetime.now().time()
    
    # Check if current hour and minute match the parameters 
    # (start the process if the current time is greater than or equal to the given time)
    return current_time.hour > hour or (current_time.hour==hour and current_time.minute >= minute)


# To store the prices
prices={}

# check find the number of lots that can be traded 
def num_lots_fun(sell_sym,buy_sym,lot_size,exchange2):
    # Fetch margin detail for order/orders
    num_lots=0
    margin_percentage=0.6
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

# Check if the order's status is pending or updated

def order_status_pending(pending_values,status_value):
    for value in pending_values:
        if(value in status_value): 
            logging.info("Order status is pending with value: {}".format(status_value))
            return True
    return False

# Check if the order is triggered or not
def order_not_triggered(order_id,status):
    print("searching for ",order_id," ",status," ",datetime.now().time())
    
    max_attempts=20
    attempts=0

    pending_status=["VALIDATION PENDING","OPEN PENDING","PUT ORDER REQ RECEIVED"]
    while attempts<=max_attempts:
        attempts+=1
        logging.info("Trying with current attempts: {}".format(attempts))
        try:
            for order in kite.orders():
                if order["order_id"] == str(order_id):
                    logging.info("order status: {} order_id {} time {}".format(order["status"],order['order_id'],datetime.now().time()))
                    if(order_status_pending(pending_status,order['status'])): continue
                    if(status in order['status']):
                        return True
                    else: return False
        except Exception as e:
            logging.info("Error in getting kite orders: {}".format(e))
        
    return True


#  Checking for order rejection
def rejected(order_id):
    logging.info("searching rejection status for {}".format(order_id))
    if(order_id==None): return True

    attempts=0
    max_attempts=20
    pending_status=["VALIDATION PENDING","OPEN PENDING","PUT ORDER REQ RECEIVED"]

    while attempts<=max_attempts:
        attempts+=1
        logging.info("Trying with current attempts: {}".format(attempts))
        try:
            for order in kite.orders():
                if order["order_id"] == str(order_id):
                    logging.info("order status: {} order_id {} time {}".format(order["status"],order['order_id'],datetime.now().time()))
                    prices[str(order_id)]=order['average_price']
                    if(order_status_pending(pending_status,order['status'])): continue
                    if("REJECTED" in order['status']):
                        return True
                    else: return False
        except Exception as e:
            logging.info("Error in getting kite orders: {}".format(e))

    return False

# Place an order
def place_order(symbol,direction,exchange,o_type,product,quantity):
    global num_order_req
    num_order_req+=1
    if(num_order_req>=16): 
        logging.info("Max number of requested orders (16) reached")
        return None
    logging.info("placing {} order current time {}".format(direction,datetime.now().time()))
    
    try:
        order_id = kite.place_order(tradingsymbol=symbol,
                                    exchange=exchange,
                                    transaction_type=kite.TRANSACTION_TYPE_BUY if direction == "buy" else kite.TRANSACTION_TYPE_SELL,
                                    quantity=quantity,
                                    variety=kite.VARIETY_REGULAR,
                                    order_type=o_type,
                                    product=product)
        
        logging.info("Order ID is: {}".format(order_id))
        return order_id
        
    except Exception as e:
        logging.info("Order placement failed: {}".format(e))
        return None

# placing a SL-Limit order
def place_sl_order(symbol,direction,exchange,o_type,product,quantity,price,trigger_price):
    global num_order_req
    num_order_req+=1
    if(num_order_req>=16): 
        logging.info("Max number of requested orders (16) reached")
        return None
    logging.info("trigger_price: {} limit_price {} time {}".format(trigger_price,price,datetime.now().time()))
    
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
        
        # return the order id
        logging.info("Order ID is: {}".format(order_id))
        return order_id
        
    except Exception as e:
        logging.info("Order placement failed: {}".format(e))
        return None


# Modify the order

def modify_order(buy_id,limit,trigger):
    try:
        order_r_id=kite.modify_order(order_id=buy_id, price=limit, trigger_price=trigger, variety=kite.VARIETY_REGULAR, order_type=kite.ORDER_TYPE_SL)
        logging.info("Order modified: {}".format(order_r_id))
        return order_r_id
    except Exception as e:
        logging.info("Error in modifying order: {}".format(e))
        return None

# Cancel the order

def cancel_order(temp_id):
    attempts=0
    max_attempts=10
    while attempts<=max_attempts:
        attempts+=1
        logging.info("Trying with current attempts: {}".format(attempts))
        try:
            cancelled_id=kite.cancel_order(variety=kite.VARIETY_REGULAR,order_id=str(temp_id))
            logging.info("order cancelled {} temp_id {}".format(cancelled_id,temp_id))
            return cancelled_id
        except Exception as e:
            logging.info("Error in cancelling order: {}".format(e))
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
    lim_ltp=round(cur_price*(1+stoploss),1)
    if(min_ltp==None): return lim_ltp
    if(lim_ltp<min_ltp): 
        min_ltp=lim_ltp
    return min_ltp


quantity=0
quantity_OTM=0
cal_quantity=True
num_orders=0
num_mod=0
percent=0.9875

trade_data={
    "sl_reached_PE":True,"sl_reached_CE":True,"SP":None,"PE_OTM_sell_status":False,"CE_OTM_sell_status":False,
    "PE_OTM_buy_order":None,"CE_OTM_buy_order":None,"tradingSym_PE_OTM":None,"tradingSym_CE_OTM":None,"token":token_sym,"symbol":symbol,
    "exit_hr":exit_time_hour,"exit_min":exit_time_min,"entry_hr":entry_time_hour,"entry_min":entry_time_min,"nearest_range":nearest_range,
    "margin_range":margin_range,"tradingSym_PE_ATM":None,"tradingSym_CE_ATM":None,"PE_buy_id":None,"CE_buy_id":None,
    "PE_LTP":None,"CE_LTP":None,"limit_PE":None,"limit_CE":None,'trigger_PE':None,'trigger_CE':None,"cur_PE_price":None,"cur_CE_price":None,
    "PE_ATM_sell_order":None,"CE_ATM_sell_order":None,"PE_sell_id":None,"CE_sell_id":None
}

token_PE=None
token_CE=None

def buy_sl_order(buy_id,sell_id,LTP,cur_price,tradingSym_ATM,limit,sl_reached,trigger,quantity):
    global stoploss,percent,num_mod

    if(buy_id==None): 
        if(sell_id and sell_id in prices): cur_price=prices[str(sell_id)] 
        LTP=cur_price
        limit=round(cur_price*(1+stoploss),1)
        trigger=round(limit*percent,1)
        if(LTP): buy_id=place_sl_order(tradingSym_ATM,"buy",kite_exchange,kite.ORDER_TYPE_SL,kite.PRODUCT_MIS,quantity,limit,trigger)
        if(rejected(buy_id)): buy_id=None

    elif(sl_reached==False):
        not_triggered=order_not_triggered(buy_id,"TRIGGER PENDING")
        if(not_triggered==False): sl_reached=True

        else:
            limit=min_val(cur_price,stoploss,limit)
            trigger=round(limit*percent,1)
            if(place_limit_order(cur_price,LTP) and buy_id!=None and not_triggered):
                if(num_mod<23):
                    temp_id=modify_order(buy_id,limit,trigger)
                    if(temp_id): 
                        LTP=cur_price
                        num_mod+=1
                else:
                    temp_id=buy_id
                    buy_id=place_sl_order(tradingSym_ATM,"buy",kite_exchange,kite.ORDER_TYPE_SL,kite.PRODUCT_MIS,quantity,limit,trigger)
                    if(rejected(buy_id)): buy_id=None
                    if(buy_id):
                        LTP=cur_price
                        cancelled_id=cancel_order(temp_id)
                        if(cancelled_id==None):
                            logging.info("order not_cancelled temp_id {}".format(temp_id))
                        # logging.info("order cancelled {} temp_id {}".format(cancelled_id,temp_id))
                    else: buy_id=temp_id

    return buy_id,LTP,limit,trigger,sl_reached

num_retry_ATM=0
num_retry_OTM=0

def retry_order(num_retry,PE_id,CE_id,direction,PE_symbol,CE_symbol):
    if num_retry>=10:
        if(PE_id):
            logging.info("Placing {} order for PE_id {}".format(direction,PE_id))
            PE_id2=place_order(PE_symbol,direction,kite_exchange,kite.ORDER_TYPE_MARKET,kite.PRODUCT_MIS,quantity)
        if(CE_id):
            logging.info("Placing {} order for CE_id {}".format(direction,CE_id))
            CE_id2=place_order(CE_symbol,direction,kite_exchange,kite.ORDER_TYPE_MARKET,kite.PRODUCT_MIS,quantity)


no_start=True
def on_ticks(ws, ticks):
#   print("tickers...")
  global num_orders,num_mod,quantity,percent,token_PE,token_CE,num_retry_OTM,num_retry_ATM,no_start,max_reconnections,cal_quantity,quantity_OTM
  for tick in ticks:
      
    try:
      
      if(no_start):
        if(is_current_time(trade_data['entry_hr'],trade_data['entry_min'])):
            logging.info("starting the process")
            no_start=False
        else: logging.info("waiting for the entry time")
        continue
      
      print(tick['instrument_token']," ",datetime.now())
      if(trade_data["PE_OTM_sell_status"] and trade_data["CE_OTM_sell_status"]): 
         max_reconnections=0
         exit("Exit")


      if(is_current_time(trade_data['exit_hr'],trade_data['exit_min'])):
        if(tick['instrument_token']==instrument_syms[trade_data['token']]):

            if(trade_data['PE_OTM_sell_status']==False): 

                PE_OTM_sell_order=place_order(trade_data['tradingSym_PE_OTM'],"sell",kite_exchange,kite.ORDER_TYPE_MARKET,kite.PRODUCT_MIS,quantity_OTM)
                if(rejected(PE_OTM_sell_order)): PE_OTM_sell_order=None
                if(PE_OTM_sell_order): trade_data['PE_OTM_sell_status']=True

            if(trade_data['CE_OTM_sell_status']==False): 

                CE_OTM_sell_order=place_order(trade_data['tradingSym_CE_OTM'],"sell",kite_exchange,kite.ORDER_TYPE_MARKET,kite.PRODUCT_MIS,quantity_OTM)
                if(rejected(CE_OTM_sell_order)): CE_OTM_sell_order=None
                if(CE_OTM_sell_order): trade_data['CE_OTM_sell_status']=True
        continue
      
      if(trade_data['sl_reached_PE'] and trade_data['sl_reached_CE']):
          if(num_orders>=3 or (is_current_time(13,00) and num_orders!=0)): continue

          if(tick['instrument_token']!=instrument_syms[trade_data['token']]): continue
          
          if(cal_quantity): trade_data['SP']=tick["last_price"]
          if(trade_data['SP']==None): continue
          
          logging.info("Actual SP: {} ltp: {} ins_token: {}".format(trade_data['SP'],tick['last_price'],tick['instrument_token']))
          trade_data['SP']=int(round(trade_data['SP']/trade_data['nearest_range'])*trade_data['nearest_range'])
          print("SP: ",trade_data['SP'])
          
          trade_data['tradingSym_PE_ATM']=trade_data['symbol']+str(trade_data['SP'])+"PE"
          trade_data['tradingSym_CE_ATM']=trade_data['symbol']+str(trade_data['SP'])+"CE"
          
          print("trading symbols ",trade_data['tradingSym_PE_ATM'],trade_data['tradingSym_CE_ATM'])

          if(trade_data['tradingSym_PE_OTM']==None): trade_data['tradingSym_PE_OTM']=trade_data['symbol']+str(trade_data['SP']-trade_data['margin_range'])+"PE"
          if(trade_data['tradingSym_CE_OTM']==None): trade_data['tradingSym_CE_OTM']=trade_data['symbol']+str(trade_data['SP']+trade_data['margin_range'])+"CE"

          if(cal_quantity):
              sell_sym=[trade_data['tradingSym_CE_ATM'],trade_data['tradingSym_PE_ATM']]
              buy_sym=[trade_data['tradingSym_PE_OTM'],trade_data['tradingSym_CE_OTM']]
              num_lot=num_lots_fun(sell_sym,buy_sym,lot_size,exchange2)
              if(num_lot==0): continue
              #num_lot=1
              cal_quantity=False
              quantity=num_lot*lot_size
              if(num_orders==0 and quantity_OTM==0): quantity_OTM=quantity

          if(trade_data['PE_OTM_buy_order']==None): trade_data['PE_OTM_buy_order']=place_order(trade_data['tradingSym_PE_OTM'],"buy",kite_exchange,kite.ORDER_TYPE_MARKET,kite.PRODUCT_MIS,quantity)
          if(trade_data['CE_OTM_buy_order']==None): trade_data['CE_OTM_buy_order']=place_order(trade_data['tradingSym_CE_OTM'],"buy",kite_exchange,kite.ORDER_TYPE_MARKET,kite.PRODUCT_MIS,quantity)
          
          if(num_orders==0 and rejected(trade_data['PE_OTM_buy_order'])): trade_data['PE_OTM_buy_order']=None
          if(num_orders==0 and rejected(trade_data['CE_OTM_buy_order'])): trade_data['CE_OTM_buy_order']=None

          trade_data['PE_buy_id']=None
          trade_data['CE_buy_id']=None
          trade_data['PE_LTP']=None
          trade_data['CE_LTP']=None
          trade_data['limit_PE']=None
          trade_data['limit_CE']=None
          trade_data['trigger_PE']=None
          trade_data['trigger_CE']=None

          if(trade_data['PE_OTM_buy_order'] and trade_data['CE_OTM_buy_order']):
              
              if(trade_data['PE_ATM_sell_order']==None): trade_data['PE_ATM_sell_order']=place_order(trade_data['tradingSym_PE_ATM'],"sell",kite_exchange,kite.ORDER_TYPE_MARKET,kite.PRODUCT_MIS,quantity)
              if(trade_data['CE_ATM_sell_order']==None): trade_data['CE_ATM_sell_order']=place_order(trade_data['tradingSym_CE_ATM'],"sell",kite_exchange,kite.ORDER_TYPE_MARKET,kite.PRODUCT_MIS,quantity)
              
              if(rejected(trade_data['PE_ATM_sell_order'])): trade_data['PE_ATM_sell_order']=None
              if(rejected(trade_data['CE_ATM_sell_order'])): trade_data['CE_ATM_sell_order']=None

              if(trade_data['PE_ATM_sell_order'] and trade_data['CE_ATM_sell_order']):
                  
                #   Resetting the parameters
                  
                  trade_data['PE_sell_id']=str(trade_data['PE_ATM_sell_order'])
                  trade_data['CE_sell_id']=str(trade_data['CE_ATM_sell_order'])

                  trade_data['sl_reached_PE']=False
                  trade_data['sl_reached_CE']=False

                  trade_data['PE_ATM_sell_order']=None
                  trade_data['CE_ATM_sell_order']=None

                  num_orders+=1

                  token_PE=instrument_syms[trade_data['tradingSym_PE_ATM']]
                  token_CE=instrument_syms[trade_data['tradingSym_CE_ATM']]

                  logging.info("token_PE {} token_CE {}".format(token_PE,token_CE))

                  num_retry_ATM=0
                  num_retry_OTM=0

                  cal_quantity=True
              else:
                  num_retry_ATM+=1
                  logging.info("retrying ATM orders {}".format(num_retry_ATM))
                  retry_order(num_retry_ATM,trade_data['PE_ATM_sell_order'],trade_data['CE_ATM_sell_order'],"buy",trade_data['tradingSym_PE_ATM'],trade_data['tradingSym_CE_ATM'])
                  if(num_retry_ATM>=10):
                      max_reconnections=0
                      exit("Exit")
          continue
    

      if(token_PE==None or token_CE==None): continue

      if(tick['instrument_token']!=token_PE and tick['instrument_token']!=token_CE): 
        #   print("token: ",tick['instrument_token'])
          continue

      elif(tick['instrument_token']==token_PE): 
          cur_PE_price=tick['last_price'] #buy_id,LTP,limit,trigger,sl_reached
        #   print("PE cur price ",cur_PE_price," time- ",tick['exchange_timestamp'])
          logging.info("PE cur price {} inst_token {} time {}".format(cur_PE_price,tick['instrument_token'],datetime.now()))
          trade_data['PE_buy_id'],trade_data['PE_LTP'],trade_data['limit_PE'],trade_data['trigger_PE'],trade_data['sl_reached_PE']=buy_sl_order(trade_data['PE_buy_id'],trade_data['PE_sell_id'],trade_data['PE_LTP'],cur_PE_price,trade_data['tradingSym_PE_ATM'],trade_data['limit_PE'],
                                                                        trade_data['sl_reached_PE'],trade_data['trigger_PE'],quantity)
            
          logging.info("PE_LTP {} limit_PE {} trigger_PE {} sl_reached_PE {}".format(trade_data['PE_LTP'],trade_data['limit_PE'],trade_data['trigger_PE'],trade_data['sl_reached_PE']))

      elif(tick['instrument_token']==token_CE): 
          cur_CE_price=tick['last_price']
          logging.info("CE cur price {} inst_token {} time {}".format(cur_CE_price,tick['instrument_token'],datetime.now()))
          trade_data['CE_buy_id'],trade_data['CE_LTP'],trade_data['limit_CE'],trade_data['trigger_CE'],trade_data['sl_reached_CE']=buy_sl_order(trade_data['CE_buy_id'],trade_data['CE_sell_id'],trade_data['CE_LTP'],cur_CE_price,trade_data['tradingSym_CE_ATM'],trade_data['limit_CE']
                                                                        ,trade_data['sl_reached_CE'],trade_data['trigger_CE'],quantity)
            
          logging.info("CE_LTP {} limit_CE {} trigger_CE {} sl_reached_CE {}".format(trade_data['CE_LTP'],trade_data['limit_CE'],trade_data['trigger_CE'],trade_data['sl_reached_CE']))

    except Exception as e:
        pass
                      
  time.sleep(2)
#   logging.debug("processing tokens {}".format(datetime.now().time()))


print("instrument_tokens ",inst_ts)
print("instrument_symbols ",instrument_syms)
def on_connect(ws, response):
  logging.info("connecting....")
  # Subscribe to a list of instrument_tokens
  ws.subscribe(inst_ts)
  ws.set_mode(ws.MODE_FULL,inst_ts)

max_reconnections=50
retry_reconnections=0
def on_close(ws, code, reason):
  global max_reconnections,retry_reconnections
  # On connection close stop the main loop
  # Reconnection will not happen after executing `ws.stop()`
  logging.info("Reconnecting..... {}".format(retry_reconnections))
  retry_reconnections+=1
  if(retry_reconnections>=max_reconnections): ws.stop()

kws.on_ticks = on_ticks
kws.on_connect = on_connect
kws.on_close = on_close
kws.connect()


# print(instruments)
