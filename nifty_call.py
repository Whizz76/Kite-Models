from breeze_connect import BreezeConnect
import pandas as pd
import urllib
print("https://api.icicidirect.com/apiuser/login?api_key="+urllib.parse.quote_plus("992248823I8852u1321hb780!36n9C06"))

isec = BreezeConnect(api_key="992248823I8852u1321hb780!36n9C06")

isec.generate_session(api_secret="28k11n7t26q!X195)912E3A62048838u", session_token="36723294")

# initializing input variables like expiry date and strike price

start_date = "2022-04-19T09:00:00.000Z"

end_date = "2022-04-19T11:00:00.000Z"

 

expiry = "2022-04-21T07:00:00.000Z"

time_interval = "5minute"

strike = 17000


# downloading historical data for call option contract

data1 = isec.get_historical_data(interval = time_interval,

                            from_date = start_date,

                            to_date = end_date,

                            stock_code = "NIFTY",

                            exchange_code = "NFO",

                            product_type = "options",

                            expiry_date = expiry,

                            right = "call",

                            strike_price = strike)

call_data = pd.DataFrame(data1["Success"])


# Transforming downloaded data into excel format

call_data.to_csv(index=False)

call_data.to_csv('Nifty_call_data_check.csv')