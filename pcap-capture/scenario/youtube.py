from webpcap.pcapcapture import QUICTrafficCapture
from webpcap.ggservice import YoutubePlayer
from logging import warn, error, info, debug, critical
import os, sys
import pandas as pd
import tomli

try:
    with open('config.toml', 'rb') as f:
        config = tomli.load(f)
        sys.path.insert(0, '/home/onos/Documents/Github/mininet-lab-tools/pcap-capture/webpcap' )
except FileNotFoundError:
    print('Config file not found')
    exit(1)

def main():
    df = pd.read_csv("")
    df_link = df['Links']
    for i in range(len(df_link)):
        get_link = YoutubePlayer(df_link[i])
        get_link.load(df_link[i])
        get_link.play_button()
        
        
if __name__ == '__main__':
    capture = QUICTrafficCapture('ens33')
    capture.capture()
    try:
        main()
    except KeyboardInterrupt:
        error('Keyboard Inter')
        sys.exit()