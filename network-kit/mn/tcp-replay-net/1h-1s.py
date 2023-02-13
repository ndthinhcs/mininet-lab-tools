import os
from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import Node, CPULimitedHost

from mininet.cli import CLI
from mininet.link import Intf, TCLink
from mininet.node import Controller, RemoteController, OVSKernelSwitch

from mininet.log import setLogLevel, info
from mininet.util import pmonitor, Popen

class NetworkTopo( Topo ):
    # Builds network topology
    def build( self, **_opts ):

        info( 'Add switches \n')
        s1 = self.addSwitch ( 's1', failMode='standalone' )
        # s1 = self.addSwitch ( 's1' )

        # Adding hosts
        info( 'Adding controller \n' )
        # h1 = self.addHost( 'h1', cpu=0.2, ip='192.168.0.2/24' )
        h1 = self.addHost( 'h1', cpu=0.2 )
        h2 = self.addHost( 'h2', cpu=0.2 )

        # Connecting hosts to switches
        for h, s in [ (h1, s1), (h2, s1)]:
            self.addLink( h, s )

def main():
    net = Mininet( controller=RemoteController,
        ipBase='192.168.1.0 /24',
        topo=NetworkTopo(), host=CPULimitedHost,
        link=TCLink,
        waitConnected=True )
    CLI( net )

if __name__ == '__main__':
    setLogLevel( 'info' )
    main()

