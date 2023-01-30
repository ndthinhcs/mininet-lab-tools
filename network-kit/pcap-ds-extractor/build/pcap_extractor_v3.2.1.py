import os
import re
import functools

import numpy as np
import pandas as pd

import time
import subprocess

import argparse as arg
import concurrent.futures

EXTRACT_PKT_PER_FLOW = 100
# MAX_STREAM_ID = -1
CONC_THREAD = 8

OVERIDE = False
HEX_TO_DEC = True
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
    decode_output = result.decode('latin-1')

    tcp, udp, gquic =  False, False, False
    if len(re.findall('tcp', decode_output)) > 0: tcp = True
    if len(re.findall('udp', decode_output)) > 0:  udp = True
    if len(re.findall('gquic', decode_output)) > 0: gquic = True
    return tcp, udp, gquic

def stream_id_len(filename, saved_filename):
    result_tcp, _ = subprocess.Popen(f'tshark -r "{filename}" -qz conv,tcp',
                               shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()

    result_udp, _ = subprocess.Popen(f'tshark -r "{filename}" -qz conv,udp',
                               shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()

    # Find the start of streams report - do not edit this string
    start_index_report = result_tcp.decode('latin-1').split('\n').index('                                                           | Frames  Bytes | | Frames  Bytes | | Frames  Bytes |      Start     |              |')
    start_index_report += 2

    tcp_stream_count = result_tcp.decode('latin-1').split('\n').__len__() - start_index_report -1
    udp_stream_count = result_udp.decode('latin-1').split('\n').__len__() - start_index_report -1

    result_tcp = result_tcp.decode('latin-1').split('\n')[start_index_report-1:-2]
    result_udp = result_udp.decode('latin-1').split('\n')[start_index_report-1:-2]

    with open(f"{saved_filename}_summary.csv", "w") as txt_file:
        txt_file.write('A_ip,A_port,B_ip,B_port,A->B_pkt,A->B_byt,B->A_pkt,B->A_byt,total_pkt,total_byt,relative_start,duration\n')
        for result in result_tcp:
            result = [x for x in result.split(' ') if x != '']
            line = f'tcp,{result[0].split(":")[0]},{result[0].split(":")[1]},{result[2].split(":")[0]},{result[2].split(":")[1]},{result[3]},{result[4]},{result[5]},{result[6]},{result[7]},{result[8]},{result[9]},{result[10]}'
            txt_file.write(f'{line} \n')
        for result in result_udp:
            result = [x for x in result.split(' ')  if x != '']
            line = f'tcp,{result[0].split(":")[0]},{result[0].split(":")[1]},{result[2].split(":")[0]},{result[2].split(":")[1]},{result[3]},{result[4]},{result[5]},{result[6]},{result[7]},{result[8]},{result[9]},{result[10]}'
            txt_file.write(f'{line} \n')
    return tcp_stream_count, udp_stream_count

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

def worker_tcp_extractor(file_path, start_stream_id, end_stream_id):
    temp_filename = f'./{TEMP_PART_LOC}/tcp_{start_stream_id}_{end_stream_id}.csv'
    cmd = f'''tshark -r "{file_path}" \
    -Y "tcp.stream>={start_stream_id} and tcp.stream<={end_stream_id} and tcp.payload" \
    -T fields \
    -e frame.time_epoch -e frame.number \
    -e tcp.stream -e ip.src -e tcp.srcport -e ip.dst -e tcp.dstport -e ip.proto -e \
    "_ws.col.Protocol" -e "_ws.col.Length" -e "_ws.col.Info" -e tcp.payload \
    -E header=n -E separator=, -E quote=d -E occurrence=f \
    >> {temp_filename}'''
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    p.wait()
    return [start_stream_id, end_stream_id], temp_filename

def worker_udp_extractor(file_path, start_stream_id, end_stream_id):
    temp_filename = f'./{TEMP_PART_LOC}/udp_{start_stream_id}_{end_stream_id}.csv'
    cmd = f'''tshark -r "{file_path}" \
    -Y "udp.stream>={start_stream_id} and udp.stream<={end_stream_id} and data" \
    -T fields \
    -e frame.time_epoch -e frame.number -e udp.stream \
    -e ip.src -e udp.srcport -e ip.dst -e udp.dstport -e ip.proto -e \
    "_ws.col.Protocol" -e "_ws.col.Length" -e "_ws.col.Info" -e data \
    -E header=n -E separator=, -E quote=d -E occurrence=f \
    >> {temp_filename}'''
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    p.wait()
    return [start_stream_id, end_stream_id], temp_filename

def worker_gquic_extractor(file_path, start_stream_id, end_stream_id):
    temp_filename = f'./{TEMP_PART_LOC}/gquic_{start_stream_id}_{end_stream_id}.csv'
    cmd = f'''tshark -r "{file_path}" \
    -Y "udp.stream>={start_stream_id} and udp.stream<={end_stream_id} and gquic.payload" \
    -T fields \
    -e frame.time_epoch -e frame.number -e udp.stream \
    -e ip.src -e udp.srcport -e ip.dst -e udp.dstport -e ip.proto -e \
    "_ws.col.Protocol" -e "_ws.col.Length" -e "_ws.col.Info" -e gquic.payload \
    -E header=n -E separator=, -E quote=d -E occurrence=f \
    >> {temp_filename}'''
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    p.wait()
    return [start_stream_id, end_stream_id], temp_filename

def merge_csv(root_file, temp_file, max_packet_per_flow = EXTRACT_PKT_PER_FLOW):
    if os.path.isfile(temp_file):
        if os.stat(temp_file).st_size != 0:
            df = pd.read_csv(temp_file, header=None, on_bad_lines='skip', encoding='latin-1', engine='python')
            df.groupby(2).head(max_packet_per_flow).to_csv(temp_file, mode='w', chunksize=128, header=False, index=False)
            subprocess.Popen(f'cat {temp_file} >> {root_file}', shell=True).wait()
        subprocess.Popen(f'rm {temp_file}', shell=True).wait()
        print('del: ', temp_file)
    return root_file

if __name__ == '__main__':

    parser = arg.ArgumentParser()
    # parser.add_argument("counter", help="An integer will be increased by 1 and printed.", type=int)

    args = parser.parse_args()

    print(ls_subfolders(PCAP_LOC))

    for file_path in ls_subfolders(PCAP_LOC):
        # construct saved file path
        _, filename = os.path.split(file_path)
        saved_loc = os.path.normpath(file_path).split(os.sep)[1:-1]
        saved_filename = f'''{SAVED_LOC}/{os.path.join(*saved_loc)}/{filename.split('.')[0]}'''

        # check if folder exists if not create it
        if not os.path.exists(os.path.join(SAVED_LOC, *saved_loc)):
            os.makedirs(os.path.join(SAVED_LOC, *saved_loc))
            print(f'''Created folder: {os.path.join(SAVED_LOC, *saved_loc)}''')

        # check if file already exists
        if os.path.exists(f'{saved_filename}.csv') or os.path.exists(f'{saved_filename}.csv') and OVERIDE is False: continue

        # split chunk of stream id range
        tcp_stream_len, udp_stream_len = stream_id_len(file_path, saved_filename)
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
            subprocess.Popen(f'touch "./{TEMP_PART_LOC}/tcp_{saved_filename}.csv"',
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
            subprocess.Popen(f'touch "./{TEMP_PART_LOC}/udp_{filename}.csv"',
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
            subprocess.Popen(f'touch "./{TEMP_PART_LOC}/gquic_{filename}.csv"',
                             stderr=subprocess.PIPE, stdout=subprocess.PIPE, shell=True).wait()
            with concurrent.futures.ThreadPoolExecutor(max_workers=CONC_THREAD) as pool:
                for start_stream_id, end_stream_id in udp_stream_split:
                    tasks.append(pool.submit(worker_gquic_extractor, file_path, start_stream_id, end_stream_id))
                    # print("waiting for tasks...", flush=True)
                for task in concurrent.futures.as_completed(tasks):
                    stream_id_range, temp_filename = task.result()
                    merge_csv(f'./{TEMP_PART_LOC}/udp_{filename}.csv', temp_filename)
                print("done udp stream", flush=True)


        # Merge csv
        result, err = subprocess.Popen(f'echo "time_epoch,frame_number,stream_id,ip_src,port_src,ip_dst,port_dst,ip_proto,protocol,length,info,data" > {saved_filename}.csv',
                        stderr=subprocess.PIPE, stdout=subprocess.PIPE, shell=True).communicate()
        print(result, err)
        merge_csv(f'{saved_filename}.csv', f'./{TEMP_PART_LOC}/tcp_{filename}.csv')
        merge_csv(f'{saved_filename}.csv', f'./{TEMP_PART_LOC}/udp_{filename}.csv')
        merge_csv(f'{saved_filename}.csv', f'./{TEMP_PART_LOC}/gquic_{filename}.csv')

        # Sorted by time_epoch
        pd.read_csv(f'{saved_filename}.csv').sort_values(by=['time_epoch']).to_csv(f'{saved_filename}.csv', index=False)

        # Padding
        if HEX_TO_DEC:
            df = pd.read_csv(f'{saved_filename}.csv')
            int_payload = convert_to_int(df['data'])
            df = pd.concat([df, pd.DataFrame(int_payload)], axis=1)
            df.to_csv(f'{saved_filename}.csv', index=False)
            del df
        print(f'Finised file {file_path} - Saved file: {saved_filename}.csv, Time taken: {time.time() - start_time}')
