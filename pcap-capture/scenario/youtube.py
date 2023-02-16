from webpcap.webpcap.pcapcapture import *
from webpcap.webpcap.ggservice import *
from logging import warn, error, info, debug
import os, sys
import pandas as pd

def main():
    df = pd.read_csv("")
    df_link = df['Links']
    for i in range(len(df_link)):
        get_link = YoutubeLivePlayer(df_link[i])
        get_link.load(df_link[i])
        get_link.play_button()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        error('Keyboard Inter')
        sys.exit()