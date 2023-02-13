from ryu.base import app_manager
from ryu.base.app_manager import lookup_service_brick
from ryu.controller import ofp_event

from ryu.controller.handler import MAIN_DISPATCHER, DEAD_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet

from ryu.lib import hub
from ryu.topology.switches import Switches, LLDPPacket
import networkx as nx
import time
import ryu.app.simple_switch_13
import array

class PacketCapture(app_manager.RyuApp):

    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(PacketCapture, self).__init__(*args, **kwargs)
        self.name = 'PacketCapture'

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):
        pkt = packet.Packet(array.array('B', ev.msg.data))
        for p in pkt.protocols:
            print(p)