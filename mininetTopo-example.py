# Name: Aaron Soh Yu Han
# Student number: A0155098W
import os
import sys
import atexit
from mininet.net import Mininet
from mininet.log import setLogLevel, info
from mininet.cli import CLI
from mininet.topo import Topo
from mininet.link import Link
from mininet.node import RemoteController
from mininet.util import dumpNodeConnections

net = None

class SingleSwitchTopo(Topo):

    def __init__(self, n=2):
        # Initialize topology
        Topo.__init__(self)

        # Read the configuration from topology.in file
        # Add hosts, switches and links
        with open('topology.in') as topoFile:
            n, m, l = [int(i) for i in next(topoFile).split()]
            for i in range(n):
                self.addHost('h%d' % (i + 1))
            for i in range(m):
                sconfig = {'dpid': "%016x" % (i + 1)}
                self.addSwitch('s%d' % (i + 1), **sconfig)
            self.linkDetails = {}
            for line in topoFile:
                h, s, b = [str(i) for i in line.split(',')]
                self.addLink(h, s)
                link = h + s
                self.linkDetails[link] = int(b)

        print self.links(True, False, True)


def startNetwork():
    info('** Creating the tree network\n')
    topo = SingleSwitchTopo(n=4)

    global net
    # modify the ip address if you are using a remote pox controller
    net = Mininet(topo=topo, link = Link,
                  controller=lambda name: RemoteController(name, ip='127.0.0.1'),
                  listenPort=6633, autoSetMacs=True)


    info('** Starting the network\n')
    net.start()

    # Create QoS Queues
    createQoS(net, topo)
    dumpNodeConnections(net.hosts)

    info('** Running CLI\n')
    CLI(net)

def createQoS(net, topo): 
    for switch in net.switches:
        for switchInterface in switch.intfList():
            if switchInterface.link:
                firstNode = switchInterface.link.intf1.node
                secondNode = switchInterface.link.intf2.node
                info(firstNode.name + secondNode.name + '\n')
                linkspeed = topo.linkDetails.get(firstNode.name + secondNode.name)
                port = switchInterface.link.intf1.name if firstNode == switch else switchInterface.link.intf2.name
                info(port)
                os.system('sudo ovs-vsctl -- set Port %s qos=@newqos \
                    -- --id=@newqos create QoS type=linux-htb other-config:max-rate=%d queues=0=@q0,1=@q1,2=@q2 \
                    -- --id=@q0 create queue other-config:max-rate=%d other-config:min-rate=%d \
                    -- --id=@q1 create queue other-config:min-rate=%d \
                    -- --id=@q2 create queue other-config:max-rate=%d' 
                    % (port, linkspeed * 1000000, linkspeed * 1000000, linkspeed * 1000000, linkspeed * 8 / 10 * 1000000, linkspeed * 5 / 10 * 1000000))

def perfTest():
    info('** Creating network and run simple performance test\n')
    topo = SingleSwitchTopo(n=4)
    # modify the ip address if you are using a remote pox controller
    net = Mininet(topo=topo, link=Link,
                  controller=lambda name: RemoteController(name, ip='127.0.0.1'),
                  listenPort=6633, autoSetMacs=True)
    net.start()
    createQoS(net, topo)
    info("Dumping host connections")
    dumpNodeConnections(net.hosts)
    info("Testing network connectivity")
    net.pingAll()

    s4, s1 = net.get('s4', 's1')

    info("Testing connectivity between s4 and s1")
    net.ping((s4,s1))
    info("Testing bandwidth between s4 and s1")
    net.iperf((s4,s1),port=8080)
    net.stop()

def stopNetwork():
    if net is not None:
        net.stop()
        # Remove QoS and Queues
        os.system('sudo ovs-vsctl --all destroy Qos')
        os.system('sudo ovs-vsctl --all destroy Queue')


if __name__ == '__main__':
    # Force cleanup on exit by registering a cleanup function
    atexit.register(stopNetwork)

    # Tell mininet to print useful information
    setLogLevel('info')
    # run option1: start some basic test on your topology such as pingall, ping and iperf.
    # perfTest()
    # run option2: start a command line to explore more of mininet, you can try different commands.
    startNetwork()
