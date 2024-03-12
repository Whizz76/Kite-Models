import os
from datetime import datetime

def get_sorted_dates(directory):
    folder_names = []
    for entry in os.scandir(directory):
        if entry.is_dir():
            folder_names.append(entry.name)

    # Convert folder names to dates
    dates = [datetime.strptime(name, "%d-%m-%Y") for name in folder_names]

    # Sort the dates
    sorted_dates = sorted(dates)

    return sorted_dates

directory = "../Data_BNF/Data_BNF"
sorted_dates = get_sorted_dates(directory)

print("Folder names in the directory sorted by date:")
for date in sorted_dates:
    print(date.strftime("%d-%m-%Y"))

def is_file_present(folder_path, file_name):
    file_path = os.path.join(folder_path, file_name)
    return os.path.exists(file_path)

folder_path="../Data_BNF/Data_BNF/01-04-2020"
file_path="BNF2020040113900CE.csv"
ans=is_file_present(folder_path,file_path)
print(ans)