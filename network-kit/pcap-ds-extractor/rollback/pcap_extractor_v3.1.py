import os
import re

import numpy as np
import pandas as pd

import time
import subprocess

import argparse as arg
import concurrent.futures

PACKET_PER_FLOW = 20
MAX_STREAM_ID = -1
CONC_THREAD = 4

OVERIDE = False
PCAP_LOC = './pcap/'
SAVED_LOC = './rawds/'
TEMP_PART_LOC = './temp_part/'

def ls_subfolders(rootdir):
    sub_folders_n_files = []
    for path, _, files in os.walk(rootdir):
        for name in files:
            sub_folders_n_files.append(os.path.join(path, name))
    return sorted(sub_folders_n_files)

def stream_id_spliter(stream_id_len, filesize):
    if filesize <= 700:
        if stream_id_len < 50:   n_split = 1
        if stream_id_len >= 50:  n_split = 5
        if stream_id_len >= 500: n_split = 15
        if stream_id_len > 5000: n_split = 50 + int(stream_id_len*0.005)
    if filesize > 700:
        if stream_id_len < 10:   n_split = 1
        if stream_id_len >= 10:  n_split = 4
        if stream_id_len >= 50:  n_split = 10
        if stream_id_len >= 100: n_split = 25
        if stream_id_len >= 500: n_split = 30 + int(stream_id_len*0.001)
        if stream_id_len > 5000: n_split = 40 + int(stream_id_len*0.0015)
    a = np.array_split(range(stream_id_len), n_split)
    return [[i[0], i[-1]] for i in a]

def ls_protocol(file):
    result, err = subprocess.Popen(f'tshark  -r {file} -qz io,phs',
                    stderr=subprocess.PIPE, stdout=subprocess.PIPE, shell=True).communicate()
    decode_output = result.decode('utf-8')

    tcp, udp, gquic =  False, False, False
    if len(re.findall('tcp', decode_output)) > 0: tcp = True
    if len(re.findall('udp', decode_output)) > 0:  udp = True
    if len(re.findall('gquic', decode_output)) > 0: gquic = True
    return tcp, udp, gquic

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


def worker_tcp_extractor(file_path, start_stream_id, end_stream_id):
    temp_filename = f'./{TEMP_PART_LOC}/tcp_{start_stream_id}_{end_stream_id}.csv'
    cmd = f'''tshark -r {file_path} \
    -Y "tcp.stream>={start_stream_id} and tcp.stream<={end_stream_id} and tcp.payload" \
    -T fields \
    -e frame.time_epoch -e frame.number \
    -e tcp.stream -e ip.src -e ip.dst -e ip.proto -e \
    "_ws.col.Protocol" -e "_ws.col.Length" -e "_ws.col.Info" -e tcp.payload \
    -E header=n -E separator=, -E quote=d -E occurrence=f \
    >> {temp_filename}'''
    # | sed -n "1,{PACKET_PER_FLOW}p" 
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    p.wait()
    return [start_stream_id, end_stream_id], temp_filename

def worker_udp_extractor(file_path, start_stream_id, end_stream_id):
    temp_filename = f'./{TEMP_PART_LOC}/udp_{start_stream_id}_{end_stream_id}.csv'
    cmd = f'''tshark -r {file_path} \
    -Y "udp.stream>={start_stream_id} and udp.stream<={end_stream_id} and data" \
    -T fields \
    -e frame.time_epoch -e frame.number -e udp.stream \
    -e ip.src -e ip.dst -e ip.proto -e \
    "_ws.col.Protocol" -e "_ws.col.Length" -e "_ws.col.Info" -e data \
    -E header=n -E separator=, -E quote=d -E occurrence=f \
    >> {temp_filename}'''
    # | sed -n "1,{PACKET_PER_FLOW}p"
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    p.wait()
    return [start_stream_id, end_stream_id], temp_filename

def worker_gquic_extractor(file_path, start_stream_id, end_stream_id):
    temp_filename = f'./{TEMP_PART_LOC}/gquic_{start_stream_id}_{end_stream_id}.csv'
    cmd = f'''tshark -r {file_path} \
    -Y "udp.stream>={start_stream_id} and udp.stream<={end_stream_id} and gquic.payload" \
    -T fields \
    -e frame.time_epoch -e frame.number -e udp.stream \
    -e ip.src -e ip.dst -e ip.proto -e \
    "_ws.col.Protocol" -e "_ws.col.Length" -e "_ws.col.Info" -e gquic.payload \
    -E header=n -E separator=, -E quote=d -E occurrence=f \
    >> {temp_filename}'''
    # | sed -n "1,{PACKET_PER_FLOW}p"
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    p.wait()
    return [start_stream_id, end_stream_id], temp_filename

def merge_csv(root_file, temp_file, max_packet_per_flow = PACKET_PER_FLOW):
    if os.path.isfile(temp_file):
        if os.stat(temp_file).st_size != 0:
            df = pd.read_csv(temp_file, header=None, on_bad_lines='skip', encoding='utf-8', engine='python')
            df.groupby(2).head(max_packet_per_flow).to_csv(temp_file, mode='w', chunksize=1, header=False, index=False)
            subprocess.Popen(f'cat {temp_file} >> {root_file}', shell=True).wait()
        subprocess.Popen(f'rm {temp_file}', shell=True).wait()
        print('del: ', temp_file)
    return root_file

if __name__ == '__main__':

    parser = arg.ArgumentParser()
    # parser.add_argument("counter", help="An integer will be increased by 1 and printed.", type=int)
    # parser.add_argument("counter", help="An integer will be increased by 1 and printed.", type=int)
    # parser.add_argument("counter", help="An integer will be increased by 1 and printed.", type=int)
    # parser.add_argument("counter", help="An integer will be increased by 1 and printed.", type=int)

    args = parser.parse_args()

    print(ls_subfolders(PCAP_LOC))

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

        # split chunk of stream id range
        tcp_stream_len, udp_stream_len = stream_id_len(file_path)
        filesize = os.stat(file_path).st_size / 10**6
        
        tcp_stream_split, udp_stream_split = [], []
        if tcp_stream_len > 0: tcp_stream_split = stream_id_spliter(tcp_stream_len, filesize)        
        if udp_stream_len > 0: udp_stream_split = stream_id_spliter(udp_stream_len, filesize)

        # check protocol existed
        exist_tcp, exist_udp, exist_gquic = ls_protocol(file_path)

        print(f'Processing file: {file_path}')
        start_time = time.time()
        
        # Filter tcp.stream
        if exist_tcp:
            tasks = []
            subprocess.Popen(f'touch ./{TEMP_PART_LOC}/tcp_{saved_filename}.csv',
                            stderr=subprocess.PIPE, stdout=subprocess.PIPE, shell=True).wait()
            with concurrent.futures.ThreadPoolExecutor(max_workers=CONC_THREAD) as pool:
                for start_stream_id, end_stream_id in tcp_stream_split:
                    tasks.append(pool.submit(worker_tcp_extractor, file_path, start_stream_id, end_stream_id))
                # print("waiting for tasks...", flush=True)
                for task in concurrent.futures.as_completed(tasks):                
                    stream_id_rang, temp_filename = task.result()
                    merge_csv(f'./{TEMP_PART_LOC}/tcp_{filename}.csv', temp_filename)

        # Filter udp.stream
        if exist_udp:
            tasks = []
            subprocess.Popen(f'touch ./{TEMP_PART_LOC}/udp_{filename}.csv', 
                             stderr=subprocess.PIPE, stdout=subprocess.PIPE, shell=True).wait()
            with concurrent.futures.ThreadPoolExecutor(max_workers=CONC_THREAD) as pool:
                for start_stream_id, end_stream_id in udp_stream_split:
                    tasks.append(pool.submit(worker_udp_extractor, file_path, start_stream_id, end_stream_id))
                    # print("waiting for tasks...", flush=True)
                for task in concurrent.futures.as_completed(tasks):
                    stream_id_range, temp_filename = task.result()
                    merge_csv(f'./{TEMP_PART_LOC}/udp_{filename}.csv', temp_filename)
                print("done udp stream", flush=True)

        # Filter gquic.stream
        if exist_gquic:
            tasks = []
            subprocess.Popen(f'touch ./{TEMP_PART_LOC}/gquic_{filename}.csv', 
                             stderr=subprocess.PIPE, stdout=subprocess.PIPE, shell=True).wait()
            with concurrent.futures.ThreadPoolExecutor(max_workers=CONC_THREAD) as pool:
                for start_stream_id, end_stream_id in udp_stream_split:
                    tasks.append(pool.submit(worker_gquic_extractor, file_path, start_stream_id, end_stream_id))
                    # print("waiting for tasks...", flush=True)
                for task in concurrent.futures.as_completed(tasks):
                    stream_id_range, temp_filename = task.result()
                    merge_csv(f'./{TEMP_PART_LOC}/udp_{filename}.csv', temp_filename)
                print("done gquic stream", flush=True)


        # Merge csv
        result, err = subprocess.Popen(f'echo "time_epoch,frame_number,stream_id,ip_src,ip_dst,ip_proto,protocol,length,info,data" > {saved_filename}', 
                        stderr=subprocess.PIPE, stdout=subprocess.PIPE, shell=True).communicate()
        print(result, err)
        merge_csv(f'{saved_filename}', f'./{TEMP_PART_LOC}/tcp_{filename}.csv')
        merge_csv(f'{saved_filename}', f'./{TEMP_PART_LOC}/udp_{filename}.csv')
        merge_csv(f'{saved_filename}', f'./{TEMP_PART_LOC}/gquic_{filename}.csv')
        
        # Sorted by time_epoch
        pd.read_csv(saved_filename).sort_values(by=['time_epoch']).to_csv(saved_filename, index=False)
        print(f'Finised file {file_path} - Saved file: {saved_filename}, Time taken: {time.time() - start_time}')