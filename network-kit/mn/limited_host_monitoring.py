import os
from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import Node, CPULimitedHost

from mininet.cli import CLI
from mininet.link import Intf
from mininet.node import Controller

from mininet.log import setLogLevel, info
from mininet.util import pmonitor

class NetworkTopo( Topo ):
    # Builds network topology
    def build( self, **_opts ):

        s1 = self.addSwitch ( 's1', failMode='standalone' )

        # Adding hosts
        h1 = self.addHost( 'h1', cpu=0.2, ip='10.0.0.1/24' )
        # h2 = self.addHost( 'd2', ip='10.0.0.1/24' )
        # h3 = self.addHost( 'd3', ip='10.0.0.1/24' )
        # h4 = self.addHost( 'd4', ip='10.0.0.1/24' )
        # h5 = self.addHost( 'd5', ip='10.0.0.1/24' )
        # h6 = self.addHost( 'd6', ip='10.0.0.1/24' )

        # Connecting hosts to switches
        self.addLink(h1, s1)
        # for d, s in [ (d1, s1), (d2, s1), (d3, s1)]:
        #     self.addLink( d, s )
        # for d, s in [ (d4, s1), (d5, s1), (d6, s1)]:
        #     self.addLink( d, s )


def run():

    topo = NetworkTopo()

    net = Mininet( topo=topo, host=CPULimitedHost, controller=None )
    net.start()
    # Make Switch act like a normal switch
    #net['s1'].cmd('ovs-ofctl add-flow s1 action=normal')
    # Make Switch act like a hub
    #net['s1'].cmd('ovs-ofctl add-flow s1 action=flood')
    # CLI( net )

    popens = {}

    hosts = net.hosts
    print(type(hosts))
    print(hosts)
    h1 = hosts[0]
    popens[h1] = h1.popen('stress --cpu 2 --timeout 20s')

    for host, line in pmonitor ( popens ):
        if host:
            print(f'{host}, {line}')
    net.stop()

if __name__ == '__main__':
    setLogLevel( 'info' )
    run()