import os
import shutil
import functools
import time
import subprocess

import pandas as pd
import numpy as np

import pyshark

FIRST_HEX = 12
EXTRACT_LEN = 149092

OVERIDE = False
PCAP_LOC = './pcap/'
SAVED_LOC = './output/'

def ls_subfolders(rootdir):
    sub_folders_n_files = []
    for path, subdirs, files in os.walk(rootdir):
        for name in files:
            sub_folders_n_files.append(os.path.join(path, name))
    return sub_folders_n_files

sub_folders_n_files = ls_subfolders(PCAP_LOC)

for file_path in sub_folders_n_files:
    
    # construct saved file path
    _, filename = os.path.split(file_path)
    saved_loc = os.path.normpath(file_path).split(os.sep)[1:-1]
    saved_filename = f'''{SAVED_LOC}/{os.path.join(*saved_loc)}/{filename.split('.')[0]}.csv'''
    
    # check if folder exists if not create it
    if not os.path.exists(os.path.join(SAVED_LOC, *saved_loc)): 
        os.makedirs(os.path.join(SAVED_LOC, *saved_loc))
        print(f'''Created folder: {os.path.join(SAVED_LOC, *saved_loc)}''')
    
    # check if file already exists
    if os.path.exists(saved_filename) and OVERIDE is False: continue
    
    # check if file too big split it:
    filesize = os.stat(file_path).st_size / 1024**2
    if filesize > 20:
        # create temporary folder to store split files
        if not os.path.exists(f'./temp_{filename}'): os.mkdir(f'./temp_{filename}')
        result, err = subprocess.Popen(f'editcap -c 10000 {file_path} ./temp_{filename}/{filename}_part',
                                       shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
        print(result.decode('utf-8'))
        print(err.decode('utf-8'))
        parts_list = ls_subfolders(f'./temp_{filename}')
    else: parts_list = [file_path]
    
    # create empty dataframe
    pd.DataFrame(columns=[['protocol'] + 
                 ['total_packet_lenght'] + 
                 np.arange(0, FIRST_HEX).tolist()]).to_csv(saved_filename, index=False)
    
    loop_times = 0 # loop counter to limit the number of loops
    start_time = time.time()
    for part in parts_list:

        capture = pyshark.FileCapture(file_path,
                                      display_filter='tcp.payload or gquic.payload')

        if loop_times > EXTRACT_LEN and EXTRACT_LEN != -1: break

        for packet in capture:
            if loop_times > EXTRACT_LEN and EXTRACT_LEN != -1: break
            loop_times += 1
            try:
                if hasattr(packet, 'gquic'):
                    protocol = ['gquic']
                    hex_payload = np.array(packet.gquic.payload.split(':')[0: FIRST_HEX])
                if hasattr(packet, 'tcp'):
                    protocol = ['tcp']
                    hex_payload = np.array(packet.tcp.payload.split(':')[0: FIRST_HEX])
                
                # Extract payload data
                int_payload = list(map(functools.partial(int, base=16), hex_payload))
                int_payload_pad = np.pad(int_payload, (0, FIRST_HEX - len(int_payload)), 'constant', constant_values=(0, 0))
                total_packet_lenght = [len(packet)]
                
                df_row = pd.DataFrame([protocol + total_packet_lenght + int_payload_pad.tolist()],
                                       columns=[['protocol'] + ['total_packet_lenght'] + np.arange(0, FIRST_HEX).tolist()])
                with open(saved_filename, 'a') as f:
                    pd.DataFrame(df_row).fillna(0).to_csv(f, mode='a', chunksize=10, header=False, index=False)
            
            except Exception as e:
                print(f'Error at packet: {packet.number}')
                print(f'Error at file {file_path}')
                print(e)
        
        # Clear memory
        capture.close()
        del capture
    
    # Remove temporary parts folder
    shutil.rmtree(f'./temp_{filename}')  
    
    # Record time
    print(f'{filename} is done in {time.time() - start_time} seconds')