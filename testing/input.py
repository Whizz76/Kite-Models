import pandas as pd
import logging
from datetime import datetime, timedelta
# data={"day":[],"instrument_token":[],"trading_symbol":[],"quantity":[],"stoploss":[],"entry_time":[],"exit_time":[],"margin_range":[],"exchange":[]}
# df=pd.DataFrame(data)
# df.to_csv("input.csv",index=False)

input_df=pd.read_csv("input.csv")
for i in range(len(input_df)):
    is_last_week=int(input_df.loc[i]["last_week"])
    if(is_last_week):
        print(input_df.loc[i])
# print(input_df)
# print("time {}".format(datetime.now()))