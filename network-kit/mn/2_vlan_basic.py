""" Notacion: hij: host j de la VLAN i h11 h12 \ / s1 -------------s2 / \ h21 h22 """

from mininet.topo import Topo

class TwoVlansBasicTopo(Topo):
    "2 vlans topology with 4 hosts and 2 switch"
    def build(self):
        s1 = self.addSwitch('s1', dpid='1')
        s2 = self.addSwitch('s2', dpid='2')
        h11 = self.addHost('h11')
        self.addLink(s1, h11, port1=1, port2=1)
        h21 = self.addHost('h21')
        self.addLink(s1, h21, port1=2, port2=1)
        h12 = self.addHost('h12')
        self.addLink(s2, h12, port1=1, port2=1)
        h22 = self.addHost('h22')
        self.addLink(s2, h22, port1=2, port2=1)
        self.addLink(s1, s2, port1=3, port2=3)


# Allows the file to be imported using `mn --custom <filename> --topo dcconfig`
topos = {
    'dcconfig': TwoVlansBasicTopo
}

# sudo mn --custom 2_vlan_basic.py --topo dcconfig --mac --controller=remote,port=6633
