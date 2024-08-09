import socket
from utils import decode_hexstring_offer_options
from model import DHCPMODEL, DHCPOFFER, DHCPREQUEST, DHCPPACK, DHCPDISCOVER
from rich.console import Console
from colorama import Fore, Back, Style, init as colorama_init


MAX_BYTES = 1024
serverPort = 67
colorama_init()

class DHCP_server(object):

    def __init__(self, args):
        self.DHCPPACKET = DHCPDISCOVER()
        self.serverPort = 67

    def start_server(self):
        try:
            print(Fore.GREEN + "[#] - " + Style.BRIGHT + "DHCP Server is starting..." + Style.RESET_ALL)
            self.s=socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
            self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR,1)
            self.s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST,1)
            self.s.bind(('0.0.0.0', self.serverPort))
        except OSError as e:
            if 'Address already in use' in e:
                print(Fore.RED + "[X] - " + Style.BRIGHT + f"Server port {self.serverPort} already in use" + Style.RESET_ALL)        

    def server_broadcast(self, args):
        while 1:
            try:
                print(Fore.YELLOW + "[!] - " + Style.BRIGHT + "Wait DHCP Discovery" + Style.RESET_ALL)
                data, address = self.s.recvfrom(MAX_BYTES)
                print(Fore.CYAN + "[✓] - " + Style.BRIGHT + "Received DHCP Discovery" + Style.RESET_ALL)
                dest = ('255.255.255.255', address[1])
                discovery = DHCPDISCOVER()
                discovery.from_raw_data(data)
                DHCPMODEL.print_table_data(discovery.dhcp_data)
                offer = DHCPOFFER(args)
                offer.set_xid(discovery.XID)                
                offer.set_chaddr(discovery.CHADDR1, discovery.CHADDR2)
                print(Fore.BLUE + "[i] - " + Style.BRIGHT + "Send DHCP Offer" + Style.RESET_ALL)
                DHCPMODEL.print_table_data(offer.dhcp_data)   
                self.s.sendto(offer.dhcp_data, dest)
                try:
                    print(Fore.YELLOW + "[!] - " + Style.BRIGHT + "Wait DHCP Request" + Style.RESET_ALL)
                    data, address = self.s.recvfrom(MAX_BYTES)
                    DHCPMODEL.print_table_data(data)
                    request_data = DHCPREQUEST()
                    request_data.from_raw_data(data)
                    print(Fore.CYAN + "[✓] - " + Style.BRIGHT + "Received DHCP Request" + Style.RESET_ALL)
                    if request_data.XID == offer.XID:
                        print(Fore.BLUE + "[i] - " + Style.BRIGHT + "Send DHCP Pack" + Style.RESET_ALL)
                        data = DHCPPACK(offer)
                        data.set_xid(request_data.XID)
                        data.set_chaddr(request_data.CHADDR1, request_data.CHADDR2)
                        DHCPMODEL.print_table_data(data.dhcp_data)
                        self.s.sendto(data.dhcp_data, dest)
                    else:
                        print(Fore.RED + "[X] - " + Style.BRIGHT + "Received DHCP Request but doesn't match transaction id" + Style.RESET_ALL)
                    break
                except:
                    raise
            except:
                raise

if __name__ == '__main__':
    dhcp_server = DHCP_server()
    dhcp_server.server_broadcast()
