import pandas as pd
import os
import logging

# test_date="2021-08-18"
test_date="2021-08-18"
test_date=test_date.split('-')
test_date=test_date[2]+'-'+test_date[1]+'-'+test_date[0]

folder_path="../Data_BNF/Data_BNF"

folder_path1 = os.path.join(folder_path, test_date)
# Check if the folder already exists
if not os.path.exists(folder_path1):
    print("Data absent")
else: print("present")
    
# df=pd.read_csv("../Data_BNF/Data_BNF/2021-08-18/BNF2021081836100PE.csv")
# print(df)