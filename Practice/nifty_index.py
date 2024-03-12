from breeze_connect import BreezeConnect
import pandas as pd
import urllib
print("https://api.icicidirect.com/apiuser/login?api_key="+urllib.parse.quote_plus("992248823I8852u1321hb780!36n9C06"))

isec = BreezeConnect(api_key="992248823I8852u1321hb780!36n9C06")

isec.generate_session(api_secret="28k11n7t26q!X195)912E3A62048838u", session_token="36723294")

# initializing input variables like expiry date and strike price

start_date = "2021-04-1T07:00:00.000Z"

end_date = "2024-04-10T18:00:00.000Z"

 

expiry = "2022-04-21T07:00:00.000Z"

time_interval = "5minute"

# downloading historical data for Nifty

data2 = isec.get_historical_data(interval = time_interval,

                            from_date = start_date,

                            to_date = end_date,

                            stock_code = "CNXBAN",

                            exchange_code = "NSE",

                            product_type = "cash")

stock_data = pd.DataFrame(data2["Success"])

 

# Transforming downloaded data into excel format

stock_data.to_csv(index=False)

stock_data.to_csv('Bnf_index_data_com19.csv')