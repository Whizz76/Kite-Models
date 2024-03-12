# from breeze_connect import BreezeConnect
import pandas as pd
# import urllib
# print("https://api.icicidirect.com/apiuser/login?api_key="+urllib.parse.quote_plus("992248823I8852u1321hb780!36n9C06"))

# isec = BreezeConnect(api_key="992248823I8852u1321hb780!36n9C06")

# isec.generate_session(api_secret="28k11n7t26q!X195)912E3A62048838u", session_token="36631057")

# # initializing input variables like expiry date and strike price

# start_date = "2022-04-19T07:00:00.000Z"

# end_date = "2022-04-19T18:00:00.000Z"

# time_interval = "1minute"

# # downloading historical data for Nifty

# data2 = isec.get_historical_data(interval = time_interval,

#                             from_date = start_date,

#                             to_date = end_date,

#                             stock_code = "NIFTY",

#                             exchange_code = "NSE",

#                             product_type = "cash")

# stock_data = pd.DataFrame(data2["Success"])
stock_data=pd.read_csv('nifty index data.csv')

for i in range(len(stock_data)):
    opening_time=stock_data.loc[i,"datetime"]
    time=opening_time.split(" ")[1][0:5]
    if(time=="10:00"):
        strike_price=stock_data.loc[i,"open"]
        strike_price=(int)((strike_price//1000)*1000)
        strike_price_500=(int)(strike_price+500.0)

        # downloading historical data for put option contract

        # data1 = isec.get_historical_data(interval = time_interval,

        #                             from_date = start_date,

        #                             to_date = end_date,

        #                             stock_code = "NIFTY",

        #                             exchange_code = "NFO",

        #                             product_type = "options",

        #                             expiry_date = expiry,

        #                             right = "put",

        #                             strike_price = strike_price)

        # put_data = pd.DataFrame(data1["Success"])

        # downloading historical data for put option contract

        # data2 = isec.get_historical_data(interval = time_interval,

        #                             from_date = start_date,

        #                             to_date = end_date,

        #                             stock_code = "NIFTY",

        #                             exchange_code = "NFO",

        #                             product_type = "options",

        #                             expiry_date = expiry,

        #                             right = "put",

        #                             strike_price = strike_price_500)

        # put_data_500 = pd.DataFrame(data2["Success"])
        

        # Transforming downloaded data into excel format


        #         # print(strike_price,strike_price_500)
        #     # print(time)