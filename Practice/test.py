import pandas as pd
data={"datetime":[],"Strike":[],"PE":[],"CE":[],"Strike_500":[],"PE_500":[],"CE_500":[]}
df=pd.DataFrame(data)
index_data=pd.read_csv("Nifty_index_data_com.csv")
for it in range(len(index_data)):
    opening_time=index_data.loc[it,"datetime"]
    time=opening_time.split(" ")[1][0:5].strip()
    date=opening_time.split(" ")[0][0:10].strip()
    if(time=="10:00"):
        strike_price=index_data.loc[it,"open"]
        strike_price=(int)((strike_price//1000)*1000)
        strike_price_500=(int)(strike_price+500.0)
        month=date[5:7].strip()
        year=date[0:4].strip()
        print(date,time,month,year,strike_price,strike_price_500)
i=0
df.loc[len(df),"datetime"]=10
df.loc[len(df),"datetime"]=20
df.to_csv(index=False)
df.to_csv("demo.csv")
print(df)