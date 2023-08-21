import socket
from utils import decode_hexstring_offer_options
from model import DHCPMODEL, DHCPOFFER, DHCPREQUEST, DHCPPACK, DHCPDISCOVER
MAX_BYTES = 1024

serverPort = 67

class DHCP_server(object):

    def server_broadcast(self):
        print("DHCP server is starting...\n")
        
        s=socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR,1)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST,1)
        s.bind(('0.0.0.0', serverPort))

        while 1:
            try:
                print("Wait DHCP discovery.\n")
                data, address = s.recvfrom(MAX_BYTES)
                print("Receive DHCP discovery.")
                dest = ('255.255.255.255', address[1])
                discovery = DHCPDISCOVER()
                discovery.from_raw_data(data)
                print("#"*20)
                DHCPMODEL.print_raw_data(data)
                print("#"*20+'\n')
                offer = DHCPOFFER()
                offer.set_xid(discovery.XID)
                offer.set_chaddr(discovery.CHADDR1, discovery.CHADDR2)
                print("Send DHCP offer.")
                print("#"*20)
                DHCPMODEL.print_raw_data(offer.dhcp_data)
                print("#"*20+'\n')
                s.sendto(offer.dhcp_data, dest)
                while 1:
                    try:
                        print("Wait DHCP request.\n")
                        data, address = s.recvfrom(MAX_BYTES)
                        DHCPMODEL.print_raw_data(data)
                        request_data = DHCPREQUEST()
                        request_data.from_raw_data(data)
                        print("Receive DHCP request.\n")
                        print("Send DHCP pack.\n")
                        data = DHCPPACK()
                        data.set_xid(request_data.XID)
                        data.set_chaddr(request_data.CHADDR1, request_data.CHADDR2)
                        DHCPMODEL.print_raw_data(data.dhcp_data)
                        s.sendto(data.dhcp_data, dest)
                        break
                    except:
                        raise
            except:
                raise
            print("[#]"*60+'\n')

if __name__ == '__main__':
    dhcp_server = DHCP_server()
    dhcp_server.server_broadcast()