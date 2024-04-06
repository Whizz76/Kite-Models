from breeze_connect import BreezeConnect
import pandas as pd
import urllib
import os
print("https://api.icicidirect.com/apiuser/login?api_key="+urllib.parse.quote_plus("992248823I8852u1321hb780!36n9C06"))

isec = BreezeConnect(api_key="992248823I8852u1321hb780!36n9C06")

isec.generate_session(api_secret="28k11n7t26q!X195)912E3A62048838u", session_token="38366814")

# initializing input variables like expiry date and strike price

start_date = "2022-07-30T07:00:00.000Z"

end_date = "2022-08-30T11:00:00.000Z"

 

expiry = "2022-04-21T07:00:00.000Z"

time_interval = "5minute"

# downloading historical data for Nifty
# CNXBAN
# NIFTY
data2 = isec.get_historical_data(interval = time_interval,

                            from_date = start_date,

                            to_date = end_date,

                            stock_code = "^VIX",

                            exchange_code = "NSE",

                            product_type = "cash")

stock_data = pd.DataFrame(data2["Success"])

 

# Transforming downloaded data into excel format
folder_path="IndexData"
stock_data.to_csv(index=False)
csv_file_name="19_23_Aug_Vix.csv"
# stock_data.to_csv('Bnf_index_data_2021.csv')
stock_data.to_csv(os.path.join(folder_path,csv_file_name),index=False)