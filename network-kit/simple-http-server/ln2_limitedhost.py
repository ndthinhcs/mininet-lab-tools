import os
from tkinter import S
from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import Node, CPULimitedHost

from mininet.cli import CLI
from mininet.link import Intf
from mininet.node import Controller

from mininet.link import TCLink

from mininet.log import setLogLevel, info
from mininet.util import pmonitor

class NetworkTopo( Topo ):
    # Builds network topology
    def build( self, **_opts ):

        s1 = self.addSwitch('s1', failMode='standalone')
        s2 = self.addSwitch('s2', failMode='standalone')
        s3 = self.addSwitch('s3', failMode='standalone')

        # Adding hosts
        h1 = self.addHost( 'h1', cpu=0.2, ip='10.0.0.1/24' )
        h2 = self.addHost( 'h2', ip='10.0.0.2/24' )
        h3 = self.addHost( 'h3', ip='10.0.0.1/24' )
        # h4 = self.addHost( 'd4', ip='10.0.0.1/24' )
        # h5 = self.addHost( 'd5', ip='10.0.0.1/24' )
        # h6 = self.addHost( 'd6', ip='10.0.0.1/24' )
        
        # Connecting hosts to switches
        # self.addLink(h1, s1)
        
        for d, s in [ (h1, s1), (h2, s2), (h3, s3) ]:
            self.addLink( d, s )
        
        for d, s in [ (s1, s2), (s2, s3)]:
            self.addLink( d, s, cls=TCLink,bw=500, delay='100ms', loss=1)    


def run():

    topo = NetworkTopo()
    
    net = Mininet( topo=topo, host=CPULimitedHost, controller=None, waitConnected=True )
    net.start()
    # Make Switch act like a normal switch
    #net['s1'].cmd('ovs-ofctl add-flow s1 action=normal')
    # Make Switch act like a hub
    #net['s1'].cmd('ovs-ofctl add-flow s1 action=flood')
    # CLI( net )

    # popens = {}

    # hosts = net.hosts

    # h1 = hosts[0]
    # popens[h1] = h1.popen('source ../venv/bin/activate; uvicorn http-client:app --host 0.0.0.0; echo 999')
    # popens[h1] = h1.popen('su onos; firefox -private')
    
    # popens[h1] = h1.popen(''' source ../venv/bin/activate && pip list && pwd''' )

    # h2 = hosts[1]
    # popens[h2] = h2.popen('source ../venv/bin/activate; uvicorn http-server:app --reload --host 0.0.0.0')

    # while True:
    # for host, line in pmonitor ( popens ):
        # if host:
            # info(f'{host.name}, {line}')
    
    CLI(net)
    net.stop()

if __name__ == '__main__':
    setLogLevel( 'info' )
    run()