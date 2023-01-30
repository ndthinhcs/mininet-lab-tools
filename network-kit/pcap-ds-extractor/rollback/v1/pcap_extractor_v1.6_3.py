import pyshark
import pandas as pd
import numpy as np

import os
import shutil
import time
import subprocess
import functools

FIRST_HEX = 128
EXTRACT_LEN = -1

OVERIDE = False
PCAP_LOC = './pcap3/'
SAVED_LOC = './csv3/'

def ls_subfolders(rootdir):
    sub_folders_n_files = []
    for path, subdirs, files in os.walk(rootdir):
        for name in files:
            sub_folders_n_files.append(os.path.join(path, name))
    return sub_folders_n_files

sub_folders = ls_subfolders(PCAP_LOC)

for file_path in sub_folders:
    
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
    if filesize > 45:
        # create temporary folder to store split files
        if not os.path.exists(f'./temp_{filename}'): os.mkdir(f'./temp_{filename}')
        result, err = subprocess.Popen(f'editcap -c 10000 {file_path} ./temp_{filename}/{filename}_part',
                                       shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
        print(result.decode('utf-8'))
        print(err.decode('utf-8'))
        parts_list = ls_subfolders(f'./temp_{filename}')
    else: parts_list = [file_path]
    
    # create empty dataframe
    pd.DataFrame(columns=[['transport_protocol'] + 
                 ['highest_layer'] + ['total_packet_lenght'] + 
                 np.arange(0, FIRST_HEX).tolist()]).to_csv(saved_filename, index=False)
    
    loop_times = 0 # loop counter to limit the number of loops
    start_time = time.time()
    for part in parts_list:

        capture = pyshark.FileCapture(file_path,
                                      display_filter='tcp.payload or gquic.payload or quic.payload or udp.stream',
                                      include_raw=True, use_json=True)

        print('Processing file: ', part)
        if loop_times > EXTRACT_LEN and EXTRACT_LEN != -1: break
        try:
            for packet in capture:
                if loop_times > EXTRACT_LEN and EXTRACT_LEN != -1: break
                loop_times += 1
                
                # get transport protocol
                if hasattr(packet, 'udp'):
                    transport_protocol = ['UDP']
                    if hasattr(packet.udp, 'gquic'):
                        highest_layer = [packet.highest_layer]
                        hex_payload = np.array(packet.gquic.payload.split(':')[0: FIRST_HEX])
                    
                    if hasattr(packet, 'quic'):
                        highest_layer = [packet.highest_layer]
                        hex_payload = np.array(packet.quic.payload.split(':')[0: FIRST_HEX])

                    if hasattr(packet, 'data'):
                        highest_layer = [packet.highest_layer]
                        hex_payload = np.array(packet.data.data.split(':')[0: FIRST_HEX])
                
                if hasattr(packet, 'tcp'):
                    transport_protocol = ['TCP']
                    highest_layer = [packet.highest_layer]
                    hex_payload = np.array(packet.tcp.payload.split(':')[0: FIRST_HEX])                
                
                else: continue

                # extract payload data
                int_payload = list(map(functools.partial(int, base=16), hex_payload))
                int_payload_pad = np.pad(int_payload, (0, FIRST_HEX - len(int_payload)), 'constant', constant_values=(0, 0))
                total_packet_lenght = [len(packet)]
                
                df_row = pd.DataFrame([transport_protocol + highest_layer + total_packet_lenght + int_payload_pad.tolist()],
                                        columns=[['transport_protocol'] + ['highest_layer'] + ['total_packet_lenght'] + np.arange(0, FIRST_HEX).tolist()])
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
    if os.path.exists(f'./temp_{filename}'): shutil.rmtree(f'./temp_{filename}')
    
    # Record time
    print(f'{filename} is done in {time.time() - start_time} seconds')