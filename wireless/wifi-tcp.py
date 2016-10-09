""" Mode: Python;
  Copyright (c) 2016
 
  This program is free software; you can redistribute it and/or modify
  it under the terms of the GNU General Public License version 2 as
  published by the Free Software Foundation;
 
  This program is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  GNU General Public License for more details.
 
  You should have received a copy of the GNU General Public License
  along with this program; if not, write to the Free Software
  Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
 
  Ported to Python By: Rohit P. Tahiliani <rohit.tahil@gmail.com>
                        Mohit P. Tahiliani <tahiliani@mnitk.edu.in>
.
  This is a simple example to test TCP over 802.11n (with MPDU aggregation enabled).
 
  Network topology:
 
    Ap    STA
    *      *
    |      |
    n1     n2
 
 In this example, an HT station sends TCP packets to the access point. 
 We report the total throughput received during a window of 100ms. 
 The user can specify the application data rate and choose the variant
 of TCP i.e. congestion control algorithm to use.
 """

import ns.applications
import ns.core
import ns.internet
import ns.mobility 
import ns.network
import ns.point_to_point
import ns.wifi


sink = ns.network.PacketSink ()                          
#The value of the last total received bytes
lastTotalRx = 0              

def CalculateThroughput():
  #Return the simulator's virtual time. 
  now = ns.core.Simulator.Now()
  #Convert Application RX Packets to MBits.
  cur = (sink.GetTotalRx() - lastTotalRx) * (8/1e5)
  print now.GetSeconds() + "s: \t" + cur + "Mbit/s"
  lastTotalRx = sink.GetTotalRx ()
  ns.core.Simulator.Schedule (ns.core.MilliSeconds (100), CalculateThroughput)



def main(argv):
  #Command line argument parser setup.
  cmd = ns.core.CommandLine()
  #Transport layer payload size in bytes. 
  cmd.payloadSize = 1472                       
  #Application layer datarate.
  cmd.dataRate = "100Mbps"                  
  #TCP variant type. 
  cmd.tcpVariant = "ns3::TcpNewReno"        
  #Physical layer bitrate. 
  cmd.phyRate = "HtMcs7"                    
  #Simulation time in seconds. 
  cmd.simulationTime = 10                      
  #PCAP Tracing is enabled or not.
  cmd.pcapTracing = "False"                          

  cmd.AddValue ("payloadSize", "Payload size in bytes", cmd.payloadSize)
  cmd.AddValue ("dataRate", "Application data ate", cmd.dataRate)
  cmd.AddValue ("tcpVariant", "Transport protocol to use: TcpTahoe, TcpReno, TcpNewReno, TcpWestwood, TcpWestwoodPlus ", cmd.tcpVariant);
  cmd.AddValue ("phyRate", "Physical layer bitrate", cmd.phyRate)
  cmd.AddValue ("simulationTime", "Simulation time in seconds", cmd.simulationTime)
  cmd.AddValue ("pcap", "Enable/disable PCAP Tracing", cmd.pcapTracing)
  cmd.Parse (sys.argv)

  #No fragmentation and no RTS/CTS 
  ns.core.Config.SetDefault ("ns3::WifiRemoteStationManager::FragmentationThreshold", ns.core.StringValue ("999999"))
  ns.core.Config.SetDefault ("ns3::WifiRemoteStationManager::RtsCtsThreshold", ns.core.StringValue ("999999"))

  #Configure TCP Options 
  ns.core.Config.SetDefault ("ns3::TcpSocket::SegmentSize", ns.core.UintegerValue (cmd.payloadSize))

  WifiMacHelper wifiMac;
  WifiHelper wifiHelper;
  wifiHelper.SetStandard (ns.wifi.WIFI_PHY_STANDARD_80211n_5GHZ)

  #Set up Legacy Channel 
  wifiChannel = ns.core.YansWifiChannelHelper ()
  wifiChannel.SetPropagationDelay ("ns3::ConstantSpeedPropagationDelayModel")
  wifiChannel.AddPropagationLoss ("ns3::FriisPropagationLossModel", "Frequency", ns.core.DoubleValue (5e9))

  #Setup Physical Layer 
  wifiPhy = ns.core.YansWifiPhyHelper.Default ()
  wifiPhy.SetChannel (wifiChannel.Create ())
  wifiPhy.Set ("TxPowerStart", ns.core.DoubleValue (10.0))
  wifiPhy.Set ("TxPowerEnd", ns.core.DoubleValue (10.0))
  wifiPhy.Set ("TxPowerLevels", ns.core.UintegerValue (1))
  wifiPhy.Set ("TxGain", ns.core.DoubleValue (0))
  wifiPhy.Set ("RxGain", ns.core.DoubleValue (0))
  wifiPhy.Set ("RxNoiseFigure", ns.core.DoubleValue (10))
  wifiPhy.Set ("CcaMode1Threshold", ns.core.DoubleValue (-79))
  wifiPhy.Set ("EnergyDetectionThreshold", ns.core.DoubleValue (-79 + 3))
  wifiPhy.SetErrorRateModel ("ns3::YansErrorRateModel")
  wifiHelper.SetRemoteStationManager ("ns3::ConstantRateWifiManager",
                                      "DataMode", ns.core.StringValue (cmd.phyRate),
                                      "ControlMode", ns.core.StringValue ("HtMcs0"))

  networkNodes = ns.network.NodeContainer ()
  networkNodes.Create (2)
  apWifiNode = Node(networkNodes.Get (0))
  staWifiNode = Node(networkNodes.Get (1))

  #Configure AP 
  ssid = ns.wifi.Ssid("network")
  wifiMac.SetType ("ns3::ApWifiMac",
                    "Ssid", SsidValue (ssid));

  apDevice = ns.network.NodeContainer ()
  apDevice = wifiHelper.Install (wifiPhy, wifiMac, apWifiNode);

  #Configure STA 
  wifiMac.SetType ("ns3::StaWifiMac",
                    "Ssid", SsidValue (ssid));

  staDevices = ns.network.NetDeviceContainer ()
  staDevices = wifiHelper.Install (wifiPhy, wifiMac, staWifiNode);

  #Mobility model 
  mobility = ns.mobility.MobilityHelper()
  positionAlloc = ns.mobility.ListPositionAllocator()
  positionAlloc.Add(ns.core.Vector3D(0.0, 0.0, 0.0))
  positionAlloc.Add(ns.core.Vector3D(1.0, 1.0, 1.0))

  mobility.SetPositionAllocator (positionAlloc);
  mobility.SetMobilityModel ("ns3::ConstantPositionMobilityModel");
  mobility.Install (apWifiNode);
  mobility.Install (staWifiNode);

  #Internet stack 
  stack = ns.internet.InternetStackHelper ()
  stack.Install (networkNodes);

  address = ns.internet.Ipv4AddressHelper ()
  address.SetBase ("10.0.0.0", "255.255.255.0");
  apInterface = ns.internet.Ipv4InterfaceContainer ()
  apInterface = address.Assign (apDevice);
  staInterface = ns.internet.Ipv4InterfaceContainer ()
  staInterface = address.Assign (staDevices);

  #Populate routing table 
  ns.internet.Ipv4GlobalRoutingHelper.PopulateRoutingTables ()

  #Install TCP Receiver on the access point 
  sinkHelper = PacketSinkHelper ("ns3::TcpSocketFactory", ns.internet.InetSocketAddress (ns.internet.Ipv4Address.GetAny (), 9))
  sinkApp = ApplicationContainer (sinkHelper.Install (apWifiNode))
  sink = ns.network.PacketSink (sinkApp.Get (0))

  #Install TCP/UDP Transmitter on the station 
  server = OnOffHelper("ns3::TcpSocketFactory", (ns.internet.InetSocketAddress (apInterface.GetAddress (0), 9)))
  server.SetAttribute ("PacketSize", ns.core.UintegerValue (payloadSize))
  server.SetAttribute ("OnTime", ns.core.StringValue ("ns3::ConstantRandomVariable[Constant=1]"))
  server.SetAttribute ("OffTime", ns.core.StringValue ("ns3::ConstantRandomVariable[Constant=0]"))
  server.SetAttribute ("DataRate", ns.network.DataRateValue (ns.network.DataRate (dataRate)))
  serverApp = ApplicationContainer(server.Install (staWifiNode))

  #Start Applications 
  sinkApp.Start (ns.core.Seconds (0.0))
  serverApp.Start (ns.core.Seconds (1.0))
  ns.core.Simulator.Schedule (ns.core.Seconds (1.1), CalculateThroughput)

  #Enable Traces 
  if pcapTracing:
      wifiPhy.SetPcapDataLinkType (ns.core.YansWifiPhyHelper.DLT_IEEE802_11_RADIO)
      wifiPhy.EnablePcap ("AccessPoint", apDevice)
      wifiPhy.EnablePcap ("Station", staDevices)
    

  #Start Simulation 
  ns.core.Simulator.Stop (ns.core.Seconds (simulationTime + 1))
  ns.core.Simulator.Run ()
  ns.core.Simulator.Destroy ()

  averageThroughput = ((sink.GetTotalRx() * 8) / (1e6  * simulationTime))
  if averageThroughput < 50:  
      ns.core.NS_LOG_ERROR ("Obtained throughput is not in the expected boundaries!")
      exit (1)
  print "Average throughput: " + averageThroughput + " Mbit/s"
  return 0

if __name__ == '__main__':
  import sys 
  sys.exit(main(sys.argv))