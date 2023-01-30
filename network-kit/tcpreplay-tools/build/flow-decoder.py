import pika
import threading, sys, os
import json, csv

from io import StringIO
import tomli

CONSUMER_QUEUE= 'hello'
CONSUMER_ROUTING_KEY = 'hello'

PRODUCER_QUEUE = 'hello2'
PRODUCER_ROUTING_KEY = 'hello2'

MAX_PACKET_PER_FLOW = 10

def string_hex_to_int(hex_string):
    return [int(hex_string[i:i+2], 16) for i in range(0, len(hex_string), 2)]


def main():
    consumer_con = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
    consumer_channel = consumer_con.channel()
    consumer_channel.queue_declare(queue=CONSUMER_QUEUE)

    producer_con = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
    producer_channel = producer_con.channel()
    producer_channel.queue_declare(queue=PRODUCER_QUEUE)

    flows = {}

    def callback(ch, method, properties, body):

        reader = csv.reader(StringIO(body.decode('latin-1')) , delimiter=',')
        # turn reader to array
        message = list(reader)[0]

        for i in range(len(message)):
            message[i] = message[i].strip('"')
        flow_key_1 = f'{message[1]}:{message[2]}-{message[3]}:{message[4]}-{message[5]}'
        flow_key_2 = f'{message[3]}:{message[4]}-{message[1]}:{message[2]}-{message[5]}'

        # review this flow_dict
        def add_flow(flow_key):
            flow_dict = {}
            if flow_key in flows and not flows[flow_key]['stop']:
                flows[flow_key]['data'].append(message[7])
                flows[flow_key]['info'].append(message[6])
                if len(flows[flow_key]['data']) == MAX_PACKET_PER_FLOW:
                    flow_dict[flow_key] = flows[flow_key]
                    producer_channel.basic_publish(exchange='',
                        routing_key=PRODUCER_ROUTING_KEY,
                        body=json.dumps(flow_dict))
                    print(json.dumps(flow_dict))
                    # print(message[7])
                    flow_dict = {}
                    flows[flow_key]['data'] = []
                    flows[flow_key]['stop'] = True

        if flow_key_1 in flows or flow_key_2 in flows:
            add_flow(flow_key_1)
            add_flow(flow_key_2)

        else:
            flows[flow_key_1] = {
                'stop': False,
                'time_epoch': message[0],
                'ip_src': message[1],
                'src_port': message[2],
                'ip_dst': message[3],
                'dst_port': message[4],
                'ip_proto': message[5],
                'info': [message[6]],
                'data': [message[7]]
            }

        # print(" [x] Received %r" % body)

    consumer_channel.basic_consume(queue='hello', on_message_callback=callback, auto_ack=True)
    print(' [*] Waiting for messages. To exit press CTRL+C')
    consumer_channel.start_consuming()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Interrupted')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)