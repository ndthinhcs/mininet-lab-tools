import subprocess
import os, sys
import time

class PcapCapture:
    def __init__(self, interface, pcap_filename, tls_key_filename, filter=None, autostop='duration:60'):
        self.interface = interface
        self.pcap_filename = pcap_filename
        self.tls_key_filename = tls_key_filename
        self.filter = filter
        self.autostop = autostop

    def capture(self):
        tshark_command = [
            'tshark',
            '-i', self.interface,
            '-o', f'ssl.keylog_file:{self.tls_key_filename}',
            '-w', self.pcap_filename
        ]
        if self.filter:
            tshark_command += ['-Y', self.filter]
        if self.autostop:
            tshark_command += ['-a', self.autostop]

        result = subprocess.Popen(tshark_command, shell=False, 
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
        return (result[0].decode('latin-1'), result[1].decode('latin-1'))

# Usage
# capture = PcapCapture("eth0", "/path/to/tls.key", "/path/to/capture.pcap")
# capture.

class AsynCapCapture(PcapCapture):
    def __init__(self, interface, pcap_filename, tls_key_filename, filter=None, autostop='duration:60'):
        super().__init__(interface, pcap_filename, tls_key_filename, filter, autostop)
        self.process = None

    def capture(self):
        tshark_command = [
            'tshark',
            '-i', self.interface,
            '-o', f'ssl.keylog_file:{self.tls_key_filename}',
            '-w', self.pcap_filename
        ]
        if self.filter:
            cmd += ['-Y', self.filter]
        if self.autostop:
            cmd += ['-a', self.autostop]
        self.process = subprocess.Popen(tshark_command, shell=False, 
                                        stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def terminate(self):
        self.process.terminate()

class QUICTrafficCapture(PcapCapture):
    def __init__(self, interface, pcap_filename=f'quic_{time.time_ns()}.pcap',
                       tls_key_filename=f'quic_tls_key_{time.time_ns()}.key', autostop='duration:60'):
        # TODO: add decode as opt
        super().__init__(interface, pcap_filename, tls_key_filename, 'quic and tcp.payload and tcp.port==443', autostop)

class HTTPTrafficCapture(PcapCapture):
    def __init__(self, interface, pcap_filename=f'http_{time.time_ns()}.pcap',
                       tls_key_filename=f'http_tls_key_{time.time_ns()}.key', autostop='duration:60'):
        super().__init__(interface, pcap_filename, tls_key_filename, 
                         'http or http2 and tcp.payload and tcp.port==443 or tcp.port==80', autostop='duration:60')

# class QUICAndHTTPTrafficCapture(PcapCapture):
#     def __init__(self, interface, pcap_filename=f'quic_http_{time.time_ns()}.pcap',
#                        tls_key_filename=f'quic_http_tls_key_{time.time_ns()}.key', autostop='duration:60'):
#         super().__init__(interface, pcap_filename, tls_key_filename, 
#                          'quic and tcp.payload and tcp.port==443 or http or http2 and tcp.payload and tcp.port==443 or tcp.port==80', autostop)