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
logging.info("Executing kiteorder4.py")

api_key = "t416qxyj6fek1upt"
kite = KiteConnect(api_key=api_key)

# Get the access token from the above response and store it in a variable
access_token = "dxfHFTxKSKTGgTro49yv5fSX5ddNfqjI"
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
    if(symbol in instruments.loc[i,'tradingsymbol'] or token_sym in instruments.loc[i,'tradingsymbol']):
        instrument_syms[instruments.loc[i,'tradingsymbol']]=instruments.loc[i,'instrument_token']

inst_ts=list(instrument_syms.values())

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

# Check if the order was successful
def order_status(order_id,status):
    for order in kite.orders():
        if order["order_id"] == str(order_id):
            if(status=="OPEN"): return order["status"] == "OPEN" or order["status"] == "TRIGGER PENDING"
            return order["status"] == status
    return False


# Place an order
def place_order(symbol,direction,exchange,o_type,product,quantity):
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
    lim_ltp=round(cur_price*(1+stoploss),1)
    if(min_ltp==None): return lim_ltp
    if(lim_ltp<min_ltp): 
        min_ltp=lim_ltp
    return min_ltp

sl_reached_PE=True
sl_reached_CE=True
SP=None
quantity=0
PE_OTM_sell_status=False
CE_OTM_sell_status=False
num_orders=0
PE_OTM_buy_order=None
CE_OTM_buy_order=None
num_mod=0
trigger_PE=None
trigger_CE=None
percent=0.9875

def buy_order(buy_id,LTP,cur_price,tradingSym_ATM,limit,sl_reached,trigger):
    global stoploss,percent,num_mod

    if(buy_id==None): 
        LTP=cur_price
        limit=round(cur_price*(1+stoploss),1)
        trigger=round(limit*percent,1)
        if(LTP): buy_id=place_sl_order(tradingSym_ATM,"buy",kite_exchange,kite.ORDER_TYPE_SL,kite.PRODUCT_MIS,quantity,limit,trigger)

    elif(sl_reached==False):
        if(order_status(buy_id,"TRIGGER PENDING")==False): sl_reached=True

        else:
            limit=min_val(cur_price,stoploss,limit)
            trigger_og=trigger
            trigger=round(limit*percent,1)
            if(place_limit_order(cur_price,LTP) and buy_id!=None and order_status(buy_id,"TRIGGER PENDING")):
                if(num_mod<23):
                    buy_id=kite.modify_order(order_id=buy_id, price=limit, trigger_price=trigger_og, variety=kite.VARIETY_REGULAR, order_type=kite.ORDER_TYPE_SL)
                    if(buy_id): 
                        LTP=cur_price
                        num_mod+=1
                else:
                    temp_id=buy_id
                    buy_id=place_sl_order(tradingSym_ATM,"buy",kite_exchange,kite.ORDER_TYPE_SL,kite.PRODUCT_MIS,quantity,limit,trigger)
                    if(buy_id):
                        LTP=cur_price
                        cancelled_id=kite.cancel_order(variety=kite.VARIETY_REGULAR,order_id=str(temp_id))
                        logging.info("order cancelled {} temp_id {}".format(cancelled_id,temp_id))

    return buy_id,LTP,limit,trigger,sl_reached

def on_ticks(ws, ticks):
  global sl_reached_CE,sl_reached_PE,SP,quantity,PE_OTM_sell_status,CE_OTM_sell_status,num_orders,PE_OTM_buy_order,CE_OTM_buy_order,percent
  global exit_time_hour,exit_time_min,entry_time_hour,entry_time_min,symbol,token_sym,nearest_range,stoploss,num_mod,trigger_PE,trigger_CE
  
  for tick in ticks:
      if(PE_OTM_sell_status and CE_OTM_sell_status): continue
      if(is_current_time(exit_time_hour,exit_time_min)):
          if(PE_OTM_buy_order): 
              PE_OTM_sell_order=place_order(tradingSym_PE_OTM,"sell",kite_exchange,kite.ORDER_TYPE_MARKET,kite.PRODUCT_MIS,quantity)
              if(PE_OTM_sell_order): PE_OTM_sell_status=True

          if(CE_OTM_buy_order): 
              CE_OTM_sell_order=place_order(tradingSym_CE_OTM,"sell",kite_exchange,kite.ORDER_TYPE_MARKET,kite.PRODUCT_MIS,quantity)
              if(CE_OTM_sell_order): CE_OTM_sell_status=True
          continue
      
      if(sl_reached_PE and sl_reached_CE):
          if(num_orders>=3 or is_current_time(13,00)): continue

          if(tick['instrument_token']==instrument_syms[token_sym]): SP=tick["last_price"]
          if(SP==None): continue

          SP=int(round(SP/nearest_range)*nearest_range)
          tradingSym_PE_ATM=symbol+str(SP)+"PE"
          tradingSym_CE_ATM=symbol+str(SP)+"CE"

          tradingSym_PE_OTM=symbol+str(SP-margin_range)+"PE"
          tradingSym_CE_OTM=symbol+str(SP+margin_range)+"CE"

          if(quantity==0):
              sell_sym=[tradingSym_CE_ATM,tradingSym_PE_ATM]
              buy_sym=[tradingSym_PE_OTM,tradingSym_CE_OTM]
              num_lot=num_lots_fun(sell_sym,buy_sym,lot_size,exchange2)
              if(num_lot==0): continue
              quantity=num_lot*lot_size

        #   if(quantity==0 or (quantity>(num_lot*lot_size))): quantity=num_lot*lot_size

          if(PE_OTM_buy_order==None): PE_OTM_buy_order=place_order(tradingSym_PE_OTM,"buy",kite_exchange,kite.ORDER_TYPE_MARKET,kite.PRODUCT_MIS,quantity)
          if(CE_OTM_buy_order==None): CE_OTM_buy_order=place_order(tradingSym_CE_OTM,"buy",kite_exchange,kite.ORDER_TYPE_MARKET,kite.PRODUCT_MIS,quantity)

          PE_buy_id=None
          CE_buy_id=None
          PE_LTP=None
          CE_LTP=None
          if(PE_OTM_buy_order and CE_OTM_buy_order):
              PE_ATM_sell_order=place_order(tradingSym_PE_ATM,"sell",kite_exchange,kite.ORDER_TYPE_MARKET,kite.PRODUCT_MIS,quantity)
              CE_ATM_sell_order=place_order(tradingSym_CE_ATM,"sell",kite_exchange,kite.ORDER_TYPE_MARKET,kite.PRODUCT_MIS,quantity)
              if(PE_ATM_sell_order and CE_ATM_sell_order):
                  sl_reached_CE=False
                  sl_reached_PE=False
                  num_orders+=1
                  time.sleep(1)
          continue
      
      token_PE=instrument_syms[tradingSym_PE_ATM]
      token_CE=instrument_syms[tradingSym_CE_ATM]

      if(tick['instrument_token']==token_PE): 
          cur_PE_price=tick['last_price']
          if(PE_buy_id==None): 
              PE_LTP=cur_PE_price
              limit_PE=round(cur_PE_price*(1+stoploss),1)
              trigger_PE=round(limit_PE*percent,1)
              if(PE_LTP): PE_buy_id=place_sl_order(tradingSym_PE_ATM,"buy",kite_exchange,kite.ORDER_TYPE_SL,kite.PRODUCT_MIS,quantity,limit_PE,trigger_PE)

          elif(sl_reached_PE==False):
              if(order_status(PE_buy_id,"TRIGGER PENDING")==False): sl_reached_PE=True

              else:
                limit_PE=min_val(cur_PE_price,stoploss,limit_PE)
                trigger_PE_og=trigger_PE
                trigger_PE=round(limit_PE*percent,1)
                if(place_limit_order(cur_PE_price,PE_LTP) and PE_buy_id!=None and order_status(PE_buy_id,"TRIGGER PENDING")):
                    if(num_mod<23):
                        PE_buy_id=kite.modify_order(order_id=PE_buy_id, price=limit_PE, trigger_price=trigger_PE_og, variety=kite.VARIETY_REGULAR, order_type=kite.ORDER_TYPE_SL)
                        if(PE_buy_id): 
                            PE_LTP=cur_PE_price
                            num_mod+=1
                    else:
                        temp_id=PE_buy_id
                        PE_buy_id=place_sl_order(tradingSym_PE_ATM,"buy",kite_exchange,kite.ORDER_TYPE_SL,kite.PRODUCT_MIS,quantity,limit_PE,trigger_PE)
                        if(PE_buy_id):
                            PE_LTP=cur_PE_price
                            cancelled_PE_id=kite.cancel_order(variety=kite.VARIETY_REGULAR,order_id=str(temp_id))
                            logging.info("order cancelled {} temp_id {}".format(cancelled_PE_id,temp_id))


      if(tick['instrument_token']==token_CE): 
          cur_CE_price=tick['last_price']
          if(CE_buy_id==None): 
              CE_LTP=cur_CE_price
              limit_CE=round(cur_CE_price*(1+stoploss),1)
              trigger_CE=round(limit_CE*percent,1)
              if(CE_LTP): CE_buy_id=place_sl_order(tradingSym_CE_ATM,"buy",kite_exchange,kite.ORDER_TYPE_SL,kite.PRODUCT_MIS,quantity,limit_CE)
              
          elif(sl_reached_CE==False):
              if(order_status(CE_buy_id,"TRIGGER PENDING")==False): sl_reached_CE=True

              else:
                limit_CE=min_val(cur_CE_price,stoploss,limit_CE)
                trigger_CE_og=trigger_CE
                trigger_CE=round(limit_CE*percent,1)
                if(place_limit_order(cur_CE_price,CE_LTP) and CE_buy_id!=None and order_status(CE_buy_id,"TRIGGER PENDING")):
                    if(num_mod<23):
                        CE_buy_id=kite.modify_order(order_id=CE_buy_id, price=limit_CE, trigger_price=trigger_CE_og, variety=kite.VARIETY_REGULAR, order_type=kite.ORDER_TYPE_SL)
                        if(CE_buy_id): 
                            CE_LTP=cur_CE_price
                            num_mod+=1
                    else:
                        temp_id=CE_buy_id
                        CE_buy_id=place_sl_order(tradingSym_CE_ATM,"buy",kite_exchange,kite.ORDER_TYPE_SL,kite.PRODUCT_MIS,quantity,limit_CE,trigger_CE)
                        if(CE_buy_id):
                            CE_LTP=cur_CE_price
                            cancelled_CE_id=kite.cancel_order(variety=kite.VARIETY_REGULAR,order_id=str(temp_id))
                            logging.info("order cancelled {} temp_id {}".format(cancelled_CE_id,temp_id))
                       
  time.sleep(1)
  logging.debug("processing tokens")

def on_connect(ws, response):
  # Subscribe to a list of instrument_tokens
  ws.subscribe(inst_ts)
  ws.set_mode(ws.MODE_FULL,inst_ts)

def on_close(ws, code, reason):
  # On connection close stop the main loop
  # Reconnection will not happen after executing `ws.stop()`
  ws.stop()

kws.on_ticks = on_ticks
kws.on_connect = on_connect
kws.on_close = on_close
kws.connect()


# print(instruments)
