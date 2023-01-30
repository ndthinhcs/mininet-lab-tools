import pyshark
import os
import numpy as np
import pandas as pd

import time
import functools
import subprocess

import nest_asyncio
nest_asyncio.apply()

PACKET_PER_FLOW = 20
BYTE_PER_PAYLOAD = 128
MAX_STREAM_ID = -1

OVERIDE = False
PCAP_LOC = './pcap2/'
SAVED_LOC = './csv2/'


def ls_subfolders(rootdir):
    sub_folders_n_files = []
    for path, _, files in os.walk(rootdir):
        for name in files:
            sub_folders_n_files.append(os.path.join(path, name))
    return sorted(sub_folders_n_files)

def stream_id_len(filename):
    result_tcp, _ = subprocess.Popen(f'tshark -r {filename} -qz conv,tcp',
                               shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()

    result_udp, _ = subprocess.Popen(f'tshark -r {filename} -qz conv,udp',
                               shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()

    # Find the start of streams report - do not edit this string
    start_index_report = result_tcp.decode('utf-8').split('\n').index('                                                           | Frames  Bytes | | Frames  Bytes | | Frames  Bytes |      Start     |              |')
    start_index_report += 3
    
    tcp_stream_count = result_tcp.decode('utf-8').split('\n').__len__() - start_index_report
    udp_stream_count = result_udp.decode('utf-8').split('\n').__len__() - start_index_report
    return tcp_stream_count, udp_stream_count

def payload_extractor(packet):
    # hex_payload =  None
    if hasattr(packet, 'udp'):
        transport_protocol = ['UDP']
        stream_id = [packet.udp.stream]
        if hasattr(packet, 'gquic'):
            if hasattr(packet.gquic, 'payload'):
                highest_layer = [packet.highest_layer]
                hex_payload = np.array(packet.gquic.payload.split(':')[0: BYTE_PER_PAYLOAD])

        if hasattr(packet, 'quic'):
            if hasattr(packet.quic, 'payload'):
                highest_layer = [packet.highest_layer]
                hex_payload = np.array(packet.quic.payload.split(':')[0: BYTE_PER_PAYLOAD])

        if hasattr(packet, 'data'):
            highest_layer = [packet.highest_layer]
            hex_payload = np.array(packet.data.data.split(':')[0: BYTE_PER_PAYLOAD])
                
    if hasattr(packet, 'tcp'):
        transport_protocol = ['TCP']
        if hasattr(packet.tcp, 'payload'):
            stream_id = [packet.tcp.stream]
            highest_layer = [packet.highest_layer]
            hex_payload = np.array(packet.tcp.payload.split(':')[0: BYTE_PER_PAYLOAD])     
    
    if 'hex_payload' not in locals(): return None, None, None, None, None, None

    # extract payload data
    int_payload = list(map(functools.partial(int, base=16), hex_payload))
    int_payload_pad = np.pad(int_payload, (0, BYTE_PER_PAYLOAD - len(int_payload)),
                             'constant', constant_values=(0, 0)).tolist()
    total_packet_lenght = [len(packet)]
    time_epoch = [packet.frame_info.time_epoch]
    
    return time_epoch, stream_id, transport_protocol, \
           highest_layer, total_packet_lenght, int_payload_pad 

if __name__ == '__main__':
    for file_path in ls_subfolders(PCAP_LOC):
        
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
        
        # create empty dataframe
        pd.DataFrame(columns=[['time_epoch'] + ['stream_id'] + 
                ['transport_protocol'] + ['highest_layer'] + ['total_packet_lenght'] + 
                np.arange(0, BYTE_PER_PAYLOAD).tolist()]).to_csv(saved_filename, index=False)

        tcp_stream_count, udp_stream_count = stream_id_len(file_path)

        print(f'Processing file: {file_path}')
        start_time = time.time()
        # Filter tcp.stream first
        for tcp_stream_id in range(tcp_stream_count):
            capture_tcp = pyshark.FileCapture(file_path,
                                            display_filter=f'tcp.stream=={tcp_stream_id} and tcp.payload',
                                            include_raw=True, use_json=True)
            for packet_index in range(PACKET_PER_FLOW):
                try: 

                    time_epoch, stream_id, transport_protocol, \
                    highest_layer, total_packet_lenght, int_payload_pad = payload_extractor(capture_tcp[packet_index])          
                    if int_payload_pad is None: continue
                    df_row = pd.DataFrame([time_epoch + stream_id + transport_protocol + \
                                        highest_layer + total_packet_lenght + int_payload_pad],
                                        columns=[['time_epoch'] + ['stream_id'] + ['transport_protocol'] + ['highest_layer'] + \
                                                 ['total_packet_lenght'] + np.arange(0, BYTE_PER_PAYLOAD).tolist()])
                    with open(saved_filename, 'a') as f:
                        pd.DataFrame(df_row).fillna(0).to_csv(f, mode='a', chunksize=1, header=False, index=False)
                except KeyError:
                    print(f'''TCP stream: {tcp_stream_id}, PKT_ID: {packet_index} - Stream ended''')
                    break
            capture_tcp.close()
            del capture_tcp

        # Then filter udp.stream
        for udp_stream_id in range(udp_stream_count):
            capture_udp = pyshark.FileCapture(file_path,
                                            display_filter=f'udp.stream=={udp_stream_id}',
                                            include_raw=True, use_json=True)
            for packet_index in range(PACKET_PER_FLOW):
                try:
                    time_epoch, stream_id, transport_protocol, \
                    highest_layer, total_packet_lenght, int_payload_pad = payload_extractor(capture_udp[packet_index])          
                    if int_payload_pad is None: continue
                    df_row = pd.DataFrame([time_epoch + stream_id + transport_protocol + \
                                        highest_layer + total_packet_lenght + int_payload_pad],
                                        columns=[['time_epoch'] + ['stream_id'] + ['transport_protocol'] + ['highest_layer'] + \
                                                 ['total_packet_lenght'] + np.arange(0, BYTE_PER_PAYLOAD).tolist()])
                    with open(saved_filename, 'a') as f:
                        pd.DataFrame(df_row).fillna(0).to_csv(f, mode='a', chunksize=1, header=False, index=False)
                except KeyError:
                    print(f'''UDP stream: {tcp_stream_id}, PKT_ID: {packet_index} - Stream ended''')
                    break
            capture_udp.close()
            del capture_udp
        
        # Sorted by time_epoch
        pd.read_csv(saved_filename).sort_values(by=['time_epoch']).to_csv(saved_filename, index=False)
        print(f'Finised file {file_path} - Saved file: {saved_filename}, Time taken: {time.time() - start_time}')