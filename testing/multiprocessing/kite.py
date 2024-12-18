import logging
import multiprocessing.process
import pandas as pd
import datetime
import time
import json
import requests
import multiprocessing
import csv
import os

logging.basicConfig(level=logging.DEBUG)

test_input=[["2024-04-22","BANKEX"],["2024-04-23","FINNIFTY"],["2024-04-23","BNF"],["2024-04-25","NIFTY50"],["2024-04-26","SENSEX"]]


filename="result.csv"
stoploss=0.6
small_range=100

input_arr=[
           {"instrument_token":"BANKEX","trading_symbol":"BANKEX","quantity":1,"stoploss":0.6,"margin_range":2000,"exchange":"BSE","last_week":0,"nearest_range":100},
           {"instrument_token":"NIFTY FIN SERVICE","trading_symbol":"FINNIFTY","quantity":1,"stoploss":0.6,"margin_range":600,"exchange":"NSE","last_week":0,"nearest_range":small_range},
           {"instrument_token":"NIFTY BANK","trading_symbol":"BANKNIFTY","quantity":1,"stoploss":0.6,"margin_range":1500,"exchange":"NSE","last_week":0,"nearest_range":100},
           {"instrument_token":"NIFTY 50","trading_symbol":"NIFTY","quantity":1,"stoploss":0.6,"margin_range":750,"exchange":"NSE","last_week":0,"nearest_range":small_range},
           {"instrument_token":"SENSEX","trading_symbol":"SENSEX","quantity":1,"stoploss":0.6,"margin_range":2000,"exchange":"BSE","last_week":0,"nearest_range":100}
           ]

def is_current_time(hour, minute,cur_time):
    # Get current time
    current_time = cur_time
    # Check if current hour and minute match the parameters
    return current_time.hour >= hour and current_time.minute >= minute

def update_csv_with_json(csv_file, json_data,column_names):
    """
    Updates the specified CSV file with the provided JSON data.

    Args:
        csv_file (str): Path to the CSV file.
        json_data (dict or list): The JSON data to be written to the CSV.
    """

    with open(csv_file, 'a', newline='') as csvfile:
        csv_writer = csv.writer(csvfile)
        if csvfile.tell() == 0:  # Check if file is empty
            csv_writer.writerow(column_names)
        # Check if the CSV file already has a header row
        try:
            csv_reader = csv.reader(open(csv_file, 'r'))
            next(csv_reader)  # Read and discard the header if it exists
        except StopIteration:
            # Write the header row if the CSV file is empty
            if isinstance(json_data, list) and len(json_data) > 0:
                header_row = json_data[0].keys()
                csv_writer.writerow(header_row)

        # Extract data from the JSON based on its structure (list or dict)
        if isinstance(json_data, list):
            for item in json_data:
                row_data = item.values()
                csv_writer.writerow(row_data)
        elif isinstance(json_data, dict):
            row_data = json_data.values()
            csv_writer.writerow(row_data)
        else:
            raise ValueError("Invalid JSON data format. Expected list or dict.")


# Get the ltp
def get_ltp(trading_symbol,test_date,cur_time,folder_path):
    print("getting ltp for trading symbol: {}".format(trading_symbol))
    file_path="./"+folder_path+"/"+test_date+"/"+trading_symbol+".csv"
    if not os.path.isfile(file_path):
        return None
    
    BNF_file=pd.read_csv(file_path)
    current_time=cur_time.strftime("%H:%M:%S")
    BNF_file=BNF_file[BNF_file["timestamp"]==test_date+" "+current_time]
    if(not BNF_file.empty): 
        BNF_file=BNF_file.values[0]
        return float(BNF_file[2])
    else: return None
    
def place_order(tradingSym,transaction_type,test_date,cur_time,folder_path):
    logging.info("direction {} time {}".format(transaction_type,cur_time))
    return get_ltp(tradingSym,test_date,cur_time,folder_path)

def sell(tradingSym,test_date,folder_path):
    time=datetime.time(15,15,0)
    return get_ltp(tradingSym,test_date,time,folder_path)

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

def get_strike_price(token,range,test_date,cur_time,folder_path):
    ltp=get_ltp(token,test_date,cur_time,folder_path)
    if(ltp==None): return None
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

def get_token_symbol(symbol,test_date):
    test_date=test_date.split("-")
    test_year=test_date[0][2:]
    test_month=test_date[1]
    if(test_month[0]=='0'): test_month=test_month[1]
    test_day=test_date[2]
    test_date=test_year+test_month+test_day
    if("50" in symbol): return symbol+"_"+test_date
    return symbol+test_date

def limit_order(test_weekday):
    s=time.time()
    test_date=test_input[test_weekday][0]
    folder_path=test_input[test_weekday][1]

    folder_path1 = os.path.join(folder_path, test_date)
    # Check if the folder already exists
    if not os.path.exists(folder_path1):
        logging.info("Data absent")
        return "Not present"

    print("started... for expiry_date {}".format(test_date))
    test_data={}
    complete_data={}
    buy_data={}
    sell_data={}

    # Initializing the input parameters
    # -----------------------------------------------------------------------
    entry_time_hour=9
    entry_time_min=35

    exit_time_hour=15
    exit_time_min=15

    input_values=input_arr[test_weekday]

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
     
    tokenSymbol=get_token_symbol(symbol,test_date)
    # -----------------------------------------------------------------------

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
        result_string=year_last_two_digits+current_date.strftime("%b").upper()

    else:

        if current_date.month<10:
            result_string = year_last_two_digits + month_index.zfill(1) + day.zfill(2)
        # Form the string in the format yymdd
        else: result_string = year_last_two_digits + month_index.zfill(2) + day.zfill(2)


    symbol=sym+result_string
    logging.info("symbol {}".format(symbol))

    cur_time=datetime.time(9,35,0)
    total_orders=0
    placeOrder=False

    while True:
        
        if is_current_time(entry_time_hour,entry_time_min,cur_time):
            placeOrder=True
            break
        else:
            logging.info("Waiting for the right time to place order")
            time.sleep(1)

    if(placeOrder):
        print(cur_time)

        PE_OTM_buy_order=None
        CE_OTM_buy_order=None
        PE_ATM_sell_order=None
        CE_ATM_sell_order=None
        PE_LTP=None
        CE_LTP=None
        limit_PE=None
        limit_CE=None
        PE_price=10000
        CE_price=10000

        not_possible=False

        while(PE_ATM_sell_order==None or CE_ATM_sell_order==None or PE_OTM_buy_order==None or 
              CE_OTM_buy_order==None):
            
            if(is_current_time(exit_time_hour,exit_time_min,cur_time)):
                not_possible=True
                break

            SP=get_strike_price(tokenSymbol,nearest_range,test_date,cur_time,folder_path)
            if(SP!=None): 

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

                PE_OTM_buy_order=place_order(tradingSym_PE_margin,"buy",test_date,cur_time,folder_path)
                CE_OTM_buy_order=place_order(tradingSym_CE_margin,"buy",test_date,cur_time,folder_path)
                
                # Check if the sell order have been executed or not
                PE_ATM_sell_status=False
                CE_ATM_sell_status=False

                if(PE_OTM_buy_order and CE_OTM_buy_order): 
                    buy_data[tradingSym_CE_margin]=CE_OTM_buy_order
                    buy_data[tradingSym_PE_margin]=PE_OTM_buy_order

                    complete_data[tradingSym_CE_margin]=1
                    complete_data[tradingSym_PE_margin]=1
                    test_data[str(tradingSym_PE_margin)]=-PE_OTM_buy_order
                    test_data[str(tradingSym_CE_margin)]=-CE_OTM_buy_order

                    PE_ATM_sell_order=place_order(tradingSym_PE,"sell",test_date,cur_time,folder_path)
                    if(PE_ATM_sell_order): 
                        sell_data[tradingSym_PE]=PE_ATM_sell_order
                        PE_LTP=PE_ATM_sell_order
                        complete_data[tradingSym_PE]=1
                        PE_ATM_sell_status=True
                        limit_PE=PE_LTP*(1+stoploss)
                        limit_PE=round(limit_PE,1)
                        test_data[str(tradingSym_PE)]=PE_LTP
                        PE_price=limit_PE
                        PE_buy_id=place_order(tradingSym_PE,"buy",test_date,cur_time,folder_path)
                

                    CE_ATM_sell_order=place_order(tradingSym_CE,"sell",test_date,cur_time,folder_path)
                    if(CE_ATM_sell_order): 
                        sell_data[tradingSym_CE]=CE_ATM_sell_order
                        CE_LTP=CE_ATM_sell_order
                        complete_data[tradingSym_CE]=1
                        CE_ATM_sell_status=True
                        limit_CE=CE_LTP*(1+stoploss)
                        limit_CE=round(limit_CE,1)
                        test_data[str(tradingSym_CE)]=CE_LTP
                        CE_price=limit_CE
                        CE_buy_id=place_order(tradingSym_CE,"buy",test_date,cur_time,folder_path)

            # Updating the time
            cur_time = (datetime.datetime.combine(datetime.date(1, 1, 1), cur_time) + datetime.timedelta(seconds=1)).time()
            logging.info("Time updated for sym {} as the strike price not found: {}".format(tokenSymbol,cur_time))

                    
        cur_time=(datetime.datetime.combine(datetime.date(1, 1, 1), cur_time) - datetime.timedelta(seconds=1)).time()
        num_lots=1
        no_order=False
        logging.info("test_data: {}".format(test_data))
        logging.info('sell_data: {}'.format(sell_data))
        if(num_lots!=0):
    
            # A paramter ti check if the stoploss order has been executed or not
            PE_limit_buy_status=False
            CE_limit_buy_status=False

            PE_after_trigger=False
            CE_after_trigger=False
            PE_triggered=False
            CE_triggered=False
            
            while not_possible==False:

                if is_current_time(exit_time_hour,exit_time_min,cur_time) or ((PE_limit_buy_status and CE_limit_buy_status) and total_orders>2):
                    logging.info("Exiting the program")
                    if(PE_OTM_buy_order): 
                        PE_OTM_sell_order=sell(tradingSym_PE_margin,test_date,folder_path)
                        if(PE_OTM_sell_order): 
                            if(tradingSym_PE_margin in complete_data): complete_data[tradingSym_PE_margin]+=1
                            if(tradingSym_PE_margin in test_data): test_data[str(tradingSym_PE_margin)]+=PE_OTM_sell_order
                            if(tradingSym_PE_margin in buy_data): sell_data[tradingSym_PE_margin]=PE_OTM_sell_order

                    if(CE_OTM_buy_order): 
                        CE_OTM_sell_order=sell(tradingSym_CE_margin,test_date,folder_path)
                        if(CE_OTM_sell_order): 
                            if (tradingSym_CE_margin in complete_data): complete_data[tradingSym_CE_margin]+=1
                            if(tradingSym_CE_margin in test_data): test_data[str(tradingSym_CE_margin)]+=CE_OTM_sell_order
                            if(tradingSym_CE_margin in buy_data): sell_data[tradingSym_CE_margin]=CE_OTM_sell_order
                    
                    break

                cur_PE_price=get_ltp(tradingSym_PE,test_date,cur_time,folder_path)
                cur_CE_price=get_ltp(tradingSym_CE,test_date,cur_time,folder_path)

                if(cur_PE_price==None or cur_CE_price==None):
                    logging.info("Data absent")
                    cur_time = (datetime.datetime.combine(datetime.date(1, 1, 1), cur_time) + datetime.timedelta(seconds=1)).time()
                    logging.info("Since data absent Time updated to: {}".format(cur_time))
                    continue


                # If sell order could not be executed or SL is hit then no need to place the buy order
                if(PE_limit_buy_status==False):
                    if(PE_ATM_sell_status==False or PE_after_trigger): PE_limit_buy_status=True
                
                if(CE_limit_buy_status==False):
                    if(CE_ATM_sell_status==False or CE_after_trigger): CE_limit_buy_status=True

                limit_PE=round(min_val(cur_PE_price,stoploss,limit_PE),1)
                limit_CE=round(min_val(cur_CE_price,stoploss,limit_CE),1)

                logging.info("cur_PE_price: {} limit_PE: {}".format(cur_PE_price,limit_PE))
                logging.info("cur_CE_price: {} limit_CE: {}".format(cur_CE_price,limit_CE))

                if(PE_after_trigger==False):
                    if(PE_triggered and cur_PE_price<=PE_price):
                        PE_after_trigger=True
                        if(tradingSym_PE in complete_data): complete_data[tradingSym_PE]+=1
                        if (tradingSym_PE in test_data): test_data[str(tradingSym_PE)]-=cur_PE_price
                        if(tradingSym_PE in sell_data): buy_data[tradingSym_PE]=cur_PE_price
                        logging.info("Price triggered for {} limit_price {} cur_price {}".format(tradingSym_PE,PE_price,cur_PE_price))
                
                if(CE_after_trigger==False):
                    if(CE_triggered and cur_CE_price<=CE_price):
                        CE_after_trigger=True
                        if(tradingSym_CE in complete_data): complete_data[tradingSym_CE]+=1
                        if(tradingSym_CE in test_data): test_data[str(tradingSym_CE)]-=cur_CE_price
                        if(tradingSym_CE in sell_data): buy_data[tradingSym_CE]=cur_CE_price
                        logging.info("Price triggered for {} limit_price {} cur_price {}".format(tradingSym_CE,CE_price,cur_CE_price))
                        

                if(PE_triggered==False): PE_triggered=is_triggered(PE_price,cur_PE_price)
                if(CE_triggered==False): CE_triggered=is_triggered(CE_price,cur_CE_price)
                    

              
                place_PE_limit_order=place_limit_order(cur_PE_price,PE_LTP)
                place_CE_limit_order=place_limit_order(cur_CE_price,CE_LTP)
                
                if(place_PE_limit_order and PE_limit_buy_status==False): 
                    if(PE_after_trigger): PE_limit_buy_status=True
                    
                    elif(PE_buy_id and PE_triggered==False): 
                        temp_id=PE_buy_id
                        PE_buy_id=place_order(tradingSym_PE,"buy",test_date,cur_time,folder_path)
                        PE_LTP=cur_PE_price
                        PE_price=limit_PE
                        logging.info("order cancelled temp_id {}".format(temp_id))

                    elif(PE_buy_id==None): 
                        PE_buy_id=place_order(tradingSym_PE,"buy",test_date,cur_time,folder_path)
                        PE_LTP=cur_PE_price
                        PE_price=limit_PE

                if(place_CE_limit_order and CE_limit_buy_status==False): 
                    if(CE_after_trigger): CE_limit_buy_status=True

                    elif(CE_buy_id and CE_triggered==False):
                        temp_id=CE_buy_id 
                        CE_buy_id=place_order(tradingSym_CE,"buy",test_date,cur_time,folder_path)
                        CE_LTP=cur_CE_price
                        logging.info("order cancelled temp_id {}".format(temp_id))
                        CE_price=limit_CE

                    elif(CE_buy_id==None):
                        CE_buy_id=place_order(tradingSym_CE,"buy",test_date,cur_time,folder_path)
                        CE_LTP=cur_CE_price
                        CE_price=limit_CE

                if(PE_limit_buy_status and CE_limit_buy_status):
                    if(no_order): 
                        logging.info("no order possible")
                        cur_time = (datetime.datetime.combine(datetime.date(1, 1, 1), cur_time) + datetime.timedelta(seconds=1)).time()
                        logging.info("Time updated for sym {} as no order possible: {}".format(tokenSymbol,cur_time))
                        continue

                    total_orders=total_orders+1
                    logging.info("total_orders: {}".format(total_orders))

                    if(total_orders>2 or is_current_time(13,00,cur_time)): 
                        logging.info("total orders exceeded or the time is 1:00 pm")
                        no_order=True
                        cur_time = (datetime.datetime.combine(datetime.date(1, 1, 1), cur_time) + datetime.timedelta(seconds=1)).time()
                        logging.info("Time updated for sym {} as no order possible: {}".format(tokenSymbol,cur_time))
                        continue

                    logging.info("limit buy orders completed, again placing the sell orders....")
                    logging.info('sell_data: {}'.format(sell_data))
                    logging.info('buy_data: {}'.format(buy_data))

                    PE_ATM_sell_order=None
                    CE_ATM_sell_order=None
                    PE_LTP=None
                    CE_LTP=None
                    limit_PE=None
                    limit_CE=None
                    PE_price=10000
                    CE_price=10000

                    not_possible=False

                    while(PE_ATM_sell_order==None or CE_ATM_sell_order==None):
                        
                        if(is_current_time(exit_time_hour,exit_time_min,cur_time)):
                            not_possible=True
                            logging.info("Exiting the program as not possible")
                            break

                        SP=get_strike_price(tokenSymbol,nearest_range,test_date,cur_time,folder_path)

                        if(SP!=None):

                            logging.info("SP: {}".format(SP))
                            CE_price=SP
                            PE_price=SP

                            tradingSym_PE=symbol+str(PE_price)+"PE"
                            tradingSym_CE=symbol+str(CE_price)+"CE"

                            logging.info("PE_sym {}".format(tradingSym_PE))
                            logging.info("CE_sym {}".format(tradingSym_CE))

                            CE_price=SP+margin_range
                            PE_price=SP-margin_range

                            # Check if the sell order have been executed or not
                            PE_ATM_sell_status=False
                            CE_ATM_sell_status=False

                            PE_ATM_sell_order=place_order(tradingSym_PE,"sell",test_date,cur_time,folder_path)
                            if(PE_ATM_sell_order): 
                                sell_data[tradingSym_PE]=PE_ATM_sell_order
                                complete_data[tradingSym_PE]=1
                                PE_LTP=PE_ATM_sell_order
                                PE_ATM_sell_status=True
                                limit_PE=PE_LTP*(1+stoploss)
                                limit_PE=round(limit_PE,1)
                                test_data[str(tradingSym_PE)]=PE_LTP
                                PE_price=limit_PE
                                PE_buy_id=place_order(tradingSym_PE,"buy",test_date,cur_time,folder_path)
                        

                            CE_ATM_sell_order=place_order(tradingSym_CE,"sell",test_date,cur_time,folder_path)
                            if(CE_ATM_sell_order): 
                                sell_data[tradingSym_CE]=CE_ATM_sell_order
                                complete_data[tradingSym_CE]=1
                                CE_LTP=CE_ATM_sell_order
                                CE_ATM_sell_status=True
                                limit_CE=CE_LTP*(1+stoploss)
                                limit_CE=round(limit_CE,1)
                                test_data[str(tradingSym_CE)]=CE_LTP
                                CE_price=limit_CE
                                CE_buy_id=place_order(tradingSym_CE,"buy",test_date,cur_time,folder_path)

                        # Updating the time
                        cur_time = (datetime.datetime.combine(datetime.date(1, 1, 1), cur_time) + datetime.timedelta(seconds=1)).time()
                        logging.info("Time updated for sym {} as the strike price not found: {}".format(tokenSymbol,cur_time))

                    cur_time=(datetime.datetime.combine(datetime.date(1, 1, 1), cur_time) - datetime.timedelta(seconds=1)).time()

                cur_time = (datetime.datetime.combine(datetime.date(1, 1, 1), cur_time) + datetime.timedelta(seconds=1)).time()
                logging.info("loop continues, time updated to: {}".format(cur_time))
                            

                # Fetch all orders
    logging.info("kite_orders: for sym: {} are- {}".format(tokenSymbol,test_data))

    net_PL=0
    column_names1=["test_date","instrument_token","net"]
    column_names2=["test_date","Symbol","net"]
    data_=[]
    add=True
    for key in test_data.keys():
        if(key in complete_data): 
            if(complete_data[key]!=2): 
                add=False
                logging.info("Order not completed for {}".format(key))
                break
                
        else: 
            add=False
            logging.info("Data not present in complete_data for {}".format(key))
            break
        net_PL+=test_data[key]
        data={"test_date":test_date,"instrument_token":key,"net":test_data[key]}
        data_.append(data)
        
    if(net_PL and add):

        for data in data_:
            update_csv_with_json(filename,data,column_names1)

        data1={"test_date":test_date,"Symbol":tokenSymbol,"net":net_PL}
        update_csv_with_json("net.csv",data1,column_names2)

    logging.info("Data updated in the csv file")
    logging.info("sell_data: for sym: {} are- {}".format(tokenSymbol,sell_data))
    logging.info("buy_data: for sym: {} are- {}".format(tokenSymbol,buy_data))
    e=time.time()-s
    logging.info("time_elapsed for sym {} is {}".format(tokenSymbol,e))


if __name__=="__main__":
    num=10
    it=0
    logging.info("Executing test6.py")
    start_time=time.time()
    
    limit_order(0)
    elapsed_time=time.time()-start_time
    logging.info("total time_taken: {}".format(elapsed_time))

    # while(it<num):
    #     p1=multiprocessing.Process(target=limit_order,args=(0,))
    #     p2=multiprocessing.Process(target=limit_order,args=(1,))
    #     p3=multiprocessing.Process(target=limit_order,args=(2,))
    #     p4=multiprocessing.Process(target=limit_order,args=(3,))
    #     p5=multiprocessing.Process(target=limit_order,args=(4,))
        

    #     p1.start()
    #     p2.start()
    #     p3.start()
    #     p4.start()
    #     p5.start()

    #     logging.info("Process started with pid %s",p1.pid)
    #     logging.info("Process started with pid %s",p2.pid)
    #     logging.info("Process started with pid %s",p3.pid)
    #     logging.info("Process started with pid %s",p4.pid)
    #     logging.info("Process started with pid %s",p5.pid)

    #     p1.join()
    #     p2.join()
    #     p3.join()
    #     p4.join()
    #     p5.join()
    #     logging.info("Process joined")

    #     elapsed_time=time.time()-start_time
    #     logging.info("total time_taken: {}".format(elapsed_time))

    #     # print("iteration ",it)

    #     # print(test_input)

    #     for input in test_input:
    #         input[0]=(datetime.datetime.strptime(input[0], "%Y-%m-%d") + datetime.timedelta(days=7)).strftime("%Y-%m-%d")
        
    #     it+=5