# Name: Aaron Soh Yu Han
# Student number: A0155098W

from pox.core import core
from pox.lib.util import dpid_to_str
import pox.openflow.libopenflow_01 as of
import pox.openflow.discovery
import pox.openflow.spanning_tree
import datetime

from pox.lib.revent import *
from pox.lib.util import dpid_to_str
from pox.lib.addresses import IPAddr, IPAddr6, EthAddr

log = core.getLogger()

class SimpleController(EventMixin):
    def __init__(self):
        self.listenTo(core.openflow)
        core.openflow_discovery.addListeners(self)
        self.forwardingTable = {}
        self.firewallPolicies ={}
        self.premiumPolicies = []

    def _handle_PacketIn(self, event):
        packet = event.parsed
        dpid = event.dpid
        src = packet.src
        dst = packet.dst
        inport = event.port

        def flood(message = None):
            msg = of.ofp_packet_out()
            msg.data = event.ofp
            msg.in_port = inport
            msg.actions.append(of.ofp_action_output(port=of.OFPP_FLOOD))
            event.connection.send(msg)

        def packetForwarding():
            queueId = 2
            if packet.type == packet.ARP_TYPE:
                srcIp = str(packet.payload.protosrc)
                dstIp = str(packet.payload.protodst)
            elif packet.type == packet.IP_TYPE:
                srcIp = str(packet.payload.srcip)
                dstIp = str(packet.payload.dstip)
                if packet.next.protocol == packet.next.TCP_PROTOCOL:
                    dstPort = str(packet.next.payload.dstport)
                    if checkFirewallRules(srcIp, dstIp, dstPort):
                        return
                if checkPremiumPolicies(dstIp) | checkPremiumPolicies(srcIp):
                    log.info("premium")
                    queueId = 1

            if dpid not in self.forwardingTable:
                self.forwardingTable[dpid]= {}
                self.forwardingTable[dpid][src] = {}
                self.forwardingTable[dpid][src]["port"] = inport
                self.forwardingTable[dpid][src]["timestamp"] = datetime.datetime.now()
            if dst in self.forwardingTable[dpid]:
                if (datetime.datetime.now() - self.forwardingTable[dpid][dst]["timestamp"]).total_seconds() > 30:
                    self.forwardingTable[dpid].pop(dst)
            if dst not in self.forwardingTable[dpid]:
                flood()
                return
            log.info("queueID: %s", queueId)
            outport = self.forwardingTable[dpid][dst]["port"]
            log.info("# S%i: Message sent: Outport %i src %s inport %s\n", dpid, outport, src, inport) 
            msg = of.ofp_flow_mod()
            msg.data = event.ofp
            msg.match = of.ofp_match.from_packet(packet, inport)
            msg.priority = 1000
            # msg.actions.append(of.ofp_action_output(port = outport))
            msg.actions.append(of.ofp_action_enqueue(port = outport, queue_id = queueId))
            event.connection.send(msg)

        def checkFirewallRules(srcIp, dstIp, port):
            if dstIp in self.firewallPolicies.keys():
                if self.firewallPolicies[dstIp]["port"].rstrip() == port:
                    if (self.firewallPolicies[dstIp]["src"] == "ALL") | (self.firewallPolicies[dstIp]["src"] == srcIp):
                        return True
            return False

        def checkPremiumPolicies(ipAddress):
           # log.info("logging %s %s %s %s", dstIp, self.premiumPolicies[0], self.premiumPolicies[1], self.premiumPolicies[2])
            for ip in self.premiumPolicies:
                if ip == ipAddress:
                    return True
            #if ipAddress in self.premiumPolicies:
                #log.info("TRUE!")
                #return True
            #else:
                #log.info("FALSE!")
            return False
            
        packetForwarding()

    def _handle_ConnectionUp(self, event):
        log.info("Switch %s has come up.", dpid_to_str(event.dpid))
        
        def readPolicies():
            with open('policy.in') as policies:
                n, m = [int(i) for i in next(policies).rstrip().split()]
                for i in range(n):
                    line = next(policies).split(',')
                    if len(line) == 2:
                        self.firewallPolicies[line[0]] = {}
                        self.firewallPolicies[line[0]]["port"] = line[1]
                        self.firewallPolicies[line[0]]["src"] = "ALL"
                    elif len(line) == 3: 
                        self.firewallPolicies[line[1]] = {}
                        self.firewallPolicies[line[1]]["port"] = line[2]
                        self.firewallPolicies[line[1]]["src"] = line[0]
                for i in range(m):
                    line = next(policies)
                    self.premiumPolicies.append(line)
        readPolicies()

def launch ():
    # Run discovery and spanning tree modules
    pox.openflow.discovery.launch()
    pox.openflow.spanning_tree.launch()

    # Starting the controller module
    core.registerNew(SimpleController)
