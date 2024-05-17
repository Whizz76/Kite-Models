import pandas as pd
result_data=[]
df=pd.DataFrame(result_data,columns=["test_date","expiry_date","token","net P/L"])
df.to_csv("result.csv",index=False)