import subprocess
import sys

import pika
import json

connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()
channel.queue_declare(queue='network-capture-test')

with open("test.log", "wb") as file:
    cmd = 'tshark -i ens33 -Y "tcp.payload" \
            -T fields \
            -e frame.time_epoch -e ip.src -e tcp.srcport -e ip.dst -e tcp.dstport -e ip.proto \
            -e _ws.col.Info -e tcp.payload \
            -E header=n -E separator=, -E quote=d -E occurrence=f \
            -a duration:20'
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
    for line in iter(lambda: process.stdout.read(1), b""):
        # split_line = line.decode('utf=8').split(',')
        print(line.decode('utf-8', 'ignore'), end=)
        # line_json = {
        #     'time_epoch': split_line[0],
        #     'ip.src': split_line[1],
        #     'port.src': split_line[2],
        #     'ip.dst': split_line[3],
        #     'port.dst': split_line[4],
        #     'ip.proto': split_line[5],
        #     'info': split_line[6],
        #     'data': split_line[7]
        # }

        # channel.basic_publish(exchange='',
        #               routing_key='',
        #               body=json.dumps(line_json))
        
        # sys.stdout.buffer.write(line)
        file.write(line)
    connection.close()
