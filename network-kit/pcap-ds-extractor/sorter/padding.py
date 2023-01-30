import numpy as np
import pandas as pd
import re
import functools
import os

# int_payload_pad
def convert_to_int(datas):
    array = []
    for data in datas:
        try:
            if data.index(':') > 0:
                split_data = data.split(':')
        except ValueError:
            split_data = re.findall('.{1,2}', data)
        int_payload = list(map(functools.partial(int, base=16), split_data))
        int_payload = int_payload[0:1460]
        int_payload_pad = np.pad(int_payload, (0, 1460-len(int_payload)), 'constant', constant_values=(0, 0))
        array.append(int_payload_pad)
    return array  

def ls_subfolders(rootdir):
    sub_folders_n_files = []
    for path, _, files in os.walk(rootdir):
        for name in files:
            sub_folders_n_files.append(os.path.join(path, name))
    return sorted(sub_folders_n_files)

SAVED_LOC = './output/'
for file_path in ls_subfolders('./rawds/'):
    # construct saved file path
    _, filename = os.path.split(file_path)
    saved_loc = os.path.normpath(file_path).split(os.sep)[1:-1]
    saved_file_loc = f'''{SAVED_LOC}/{os.path.join(*saved_loc)}/{filename.split('.')[0]}.csv'''
        
    # check if folder exists if not create it
    if not os.path.exists(os.path.join(SAVED_LOC, *saved_loc)): 
        os.makedirs(os.path.join(SAVED_LOC, *saved_loc))
        print(f'''Created folder: {os.path.join(SAVED_LOC, *saved_loc)}''')

    # check if file already exists
    if os.path.exists(saved_file_loc): continue
    print(filename)
    
    df = pd.read_csv(file_path)
    int_payload = convert_to_int(df['data'])
    df = pd.concat([df, pd.DataFrame(int_payload)], axis=1)
    df.to_csv(saved_file_loc, index=False)