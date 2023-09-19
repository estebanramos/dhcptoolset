import argparse
from dhcp_server import DHCP_server

def rogue_dhcp_action(args):
    print(args.server)
    rogue_server = DHCP_server(args)
    rogue_server.server_broadcast(args)



parser = argparse.ArgumentParser(description="DHCP Toolset")
subparsers = parser.add_subparsers(help='Type of script')
dhcp_server_parser = subparsers.add_parser('rogue-dhcp', help='Deploy Rogue DHCP')
dhcp_server_parser.set_defaults(func=rogue_dhcp_action)
dhcp_server_parser.add_argument('-s', '--server', help = 'DHCP Server', default = '192.168.1.1')
dhcp_server_parser.add_argument('-n', '--network', help = 'Network with Netmask to take IPs from', default = '192.168.1.1/24')
dhcp_server_parser.add_argument('-r', '--router', help = 'Default Gateway IP', default = '192.168.1.1')
dhcp_server_parser.add_argument('-o', '--offer', help = 'IP to offer to Clients', default = '192.168.1.121')


dhcp_client_parser = subparsers.add_parser('fake-client', help='Send fake DHCP requests to the network')
args = parser.parse_args()
args.func(args)
config = vars(args)
#print(config)

