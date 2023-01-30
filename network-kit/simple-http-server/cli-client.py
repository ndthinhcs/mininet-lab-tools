from ipaddress import ip_address
import requests as rq
import argparse

import io, os, sys

import time
import subprocess
import logging

def generate_big_file(filename, size=100):
    '''
        Create random file with name and
        size in unit MB
    '''
    with open(f'{filename}', 'wb') as f:
        f.seek(1024 * 1024 * size -1)
        f.write(str.encode("0"))

def upload_speed(url, size=100):
    '''
        url with default upload size = 100mb
        filename id is unix time
        speed unit: Mbit/s
    '''
    id_filename = str(int(time.time()*10**6))
    filename = f'temp/{id_filename}'
    generate_big_file(filename, size)
    with open(f'{filename}', 'r') as upload_file:
        start_time = time.time()
        respone = rq.post(url, files={'file': upload_file})
        end_time = time.time()
    os.remove(filename)
    
    speed = -1
    if respone.status_code == 200:
        speed = size*8 / (end_time - start_time)
        speed = round(speed, 5)
    return speed

def download_file(url, size=100):
    '''
        url with default download size = 100mb
        filename id is unix time
        speed unit: Mbit/s
    '''
    id_filename = str(int(time.time()*10**6))
    filename = f'temp/{id_filename}'
    with rq.get(url, stream=True) as respone:
        start_time = time.time()
        respone.raise_for_status()
        with open(filename, 'wb') as f:
            for chunk in respone.iter_content(chunk_size=8192): 
                f.write(chunk)
        end_time = time.time()
        
        speed = -1
        if respone.status_code == 200:
            size = os.path.getsize(filename)
            speed = size/1024/1024*8 / (end_time - start_time)
            speed = round(speed, 5)
        os.remove(filename)
    return speed


def main():
    parser = argparse.ArgumentParser(description='simple cli client')

    parser.add_argument('ip', type=str,
                        help='ip address of server')
    
    parser.add_argument('-m', '--mode', type=str, default='',
                        help='upload(short u) or download(short d) or both(short b)')
    
    parser.add_argument('-p', '--ping', action='store_true',
                        help='get server latency')
    
    parser.add_argument('-s', '--size', type=int, default=100)

    parser.add_argument('-srt', '--server-respone-time',
                        action='store_true', help='get server respone time')

    parser.add_argument('-fl', '--file-log',
                        type=int, help='file log ouput')

    # try:
    args = parser.parse_args()
    url = f'http://{args.ip}:8000'
    # log = logging.Logger()

    for _ in range(1):
        log_output = ''
        if args.ping is True:
            ping_ouput = ping = subprocess.getoutput(f'''ping -c1 {args.ip} | perl -ne '/time=([\d\.]+) ms/ && printf "%.0f\n", $1' ''')
            if ping != '' or not None:
                ping = sum([int(x) for x in ping_ouput.split('\n')]) / 3
                ping = ping_ouput
                log_output += f'ping: {ping} ms \n'

        if args.mode != '':
            if any(x in args.mode.split(',')  for x in ['u', 'upload', 'b', 'both']):
                upload = upload_speed(f'{url}/upload', args.size)
                log_output += f'upload: {upload} Mbit/s \n'

            if any(x in args.mode.split(',') for x in ['d', 'download', 'b', 'both']):
                download = download_file(f'{url}/download/{args.size}')
                log_output += f'download: {download} Mbit/s \n'

        if args.server_respone_time is True:
            client_send_time = int (time.time() * 1000)
            respone = rq.get(f'{url}/respone_time')
            server_recive_time = int(respone.json()['time'])
            client_recive_time = int (time.time() * 1000)
            rsp_time =  (server_recive_time - client_send_time) + (client_recive_time - server_recive_time) 
            log_output += f'respone_time: {rsp_time} ms \n'
        
        print(log_output)
 
if __name__ == '__main__':
    main()