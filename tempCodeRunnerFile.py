import os

def get_folder_names(directory):
    folder_names = []
    for entry in os.scandir(directory):
        if entry.is_dir():
            folder_names.append(entry.name)
    return folder_names

directory = "./Data_BNF/Data_BNF"
folder_names = get_folder_names(directory)
print("Folder names in the directory:")
for name in folder_names:
    print(name)
