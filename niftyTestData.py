import pandas as pd
import os
from datetime import datetime, timedelta

df1=pd.read_csv("Nifty_index_data_com.csv")
df1["date_col"]=df1["datetime"]

df1=df1[df1["date_col"].apply(lambda x:datetime.strptime(x.split(" ")[0][0:11],"%Y-%m-%d"))>=pd.Timestamp('2022-06-01')].reset_index(drop=True)
df1=df1[df1["date_col"].apply(lambda x:datetime.strptime(x.split(" ")[0][0:11],"%Y-%m-%d"))<=pd.Timestamp('2023-07-01')].reset_index(drop=True)
df1.drop('date_col', axis=1, inplace=True)

index_data=df1
print(index_data)

index_data.to_csv("Jun22ToJun23NiftyIndex.csv",index=False)