import argparse, utils, sys
from dhcp_server import DHCP_server

def is_valid_interface(value):
    if not utils.valid_interface(value):
        raise argparse.ArgumentTypeError(f"A Valid Interface must be provided \n Valid interfaces {utils.interfaces()}")
    return value

def is_valid_ip(value):
    if utils.valid_ip(value):
        return str(value)
    else:
        raise argparse.ArgumentTypeError(f"'{value}' is not a valid IPv4 address")

def rogue_dhcp_action(args):
    network_info = utils.get_main_network_info()
    if args.server is None:
        args.server = utils.get_default_gateway(args.iface)
    print(f"Server: {args.server}")

    if args.router is None:
        args.router = utils.get_default_gateway(args.iface)
    print(f"Router: {args.router}")

    if args.offer is None:
        args.offer = utils.generate_random_ip(network_info['Interface'])
    print(f"Offer: {args.offer}")
    rogue_server = DHCP_server(args)
    rogue_server.start_server()
    rogue_server.server_broadcast(args)



parser = argparse.ArgumentParser(description="DHCP Toolset")
subparsers = parser.add_subparsers(help='Type of script')
dhcp_server_parser = subparsers.add_parser('rogue-dhcp', help='Deploy Rogue DHCP')
dhcp_server_parser.set_defaults(func=rogue_dhcp_action)
dhcp_server_parser.add_argument('-i', '--iface', help = 'Network interface to listen', required = True, type=is_valid_interface)
dhcp_server_parser.add_argument('-s', '--server', help = 'DHCP Server', required = False, type=is_valid_ip)
dhcp_server_parser.add_argument('-r', '--router', help = 'Default Gateway IP', required = False, type=is_valid_ip)
dhcp_server_parser.add_argument('-o', '--offer', help = 'IP to offer to Clients. Defaults to random ip', type=is_valid_ip)


dhcp_client_parser = subparsers.add_parser('fake-client', help='Send fake DHCP requests to the network')
if len(sys.argv) == 1:
    parser.print_help()
else:
    try:
        args = parser.parse_args()
        args.func(args)
    except argparse.ArgumentTypeError as e:
        print(f"Error: {e}")

