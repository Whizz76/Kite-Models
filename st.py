import datetime
import time
import pandas as pd

token="BANKNIFTY"
ex=datetime.datetime.strptime("2024-04-16",'%Y-%m-%d')
y=str(ex.year)[-2:]
m=str(ex.month)
t="NIFTY BANK"
# if m<10: m=m[1]
d=ex.day
print(m)
f=token+y+m+str(d).zfill(2)
print(f)
df=pd.read_csv("instruments.csv")
token="NIFTY BANK"
i=df[df['tradingsymbol']==token]
i=i.iloc[0]['tradingsymbol']
print(i)
ins_t={}
for i in range(len(df)):
    if(f in df.loc[i,'tradingsymbol'] or t in df.loc[i,'tradingsymbol']):
        ins_t[df.loc[i,'tradingsymbol']]=df.loc[i,'instrument_token']
# df=df[df['tradingsymbol'].str.contains(f)]['instrument_token']
# print(df)

# for data in df:
#     print(data)
#     # ins_t[data['instrument_token']]=data['tradingsymbol']
# # df.append(i)
# # print(df)
# # print(len(df))
# print(ins_t)
# print(len(ins_t))
tt=list(ins_t.values())
print(tt)
print(len(tt))
# # print(f)
# # print(d)
# # print(ex)
# # print(datetime.datetime.now().year)