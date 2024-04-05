import os
import pandas as pd

# Directory where the CSV files are located
source_directory = 'outputFiles/june1923/BNF/'

# New CSV file to create after merging _100 files
merged_100_csv_file = os.path.join(source_directory, 'merged_100.csv')

# New CSV file to create after merging the rest of the files
merged_others_csv_file = os.path.join(source_directory, 'merged_others.csv')

# Lists to hold data from each CSV file category
dataframes_100 = []
dataframes_others = []

# List all files in the directory
csv_files = [file for file in os.listdir(source_directory) if file.endswith('.csv')]

# Read each CSV file and append to the respective list
for file in csv_files:
    file_path = os.path.join(source_directory, file)
    if file.endswith('_100.csv'):
        df = pd.read_csv(file_path)
        dataframes_100.append(df)
    else:
        df = pd.read_csv(file_path)
        dataframes_others.append(df)

# Concatenate all dataframes in the _100 category into a single dataframe and write to CSV
if dataframes_100:
    merged_df_100 = pd.concat(dataframes_100, ignore_index=True)
    merged_df_100.to_csv(merged_100_csv_file, index=False)
    print(f"Files ending with _100.csv have been merged into {merged_100_csv_file}")
else:
    print("No files ending with _100.csv to merge.")

# Concatenate all dataframes in the other category into a single dataframe and write to CSV
if dataframes_others:
    merged_df_others = pd.concat(dataframes_others, ignore_index=True)
    merged_df_others.to_csv(merged_others_csv_file, index=False)
    print(f"The remaining .csv files have been merged into {merged_others_csv_file}")
else:
    print("No other .csv files to merge.")
