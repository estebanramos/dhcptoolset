import argparse, utils, sys
import os
from dhcp_server import DHCP_server, PortInUseError
from rich.console import Console
from rich.table import Table
from rich import box
from colorama import Fore, Back, Style, init as colorama_init

colorama_init()

def check_root_privileges():
    """Check if the script is running with root/administrator privileges.
    
    Returns:
        bool: True if running as root/admin, False otherwise
    """
    return os.geteuid() == 0 if hasattr(os, 'geteuid') else False

def is_valid_interface(value):
    """Validate that the provided network interface exists on the system.
    
    Args:
        value: Interface name to validate
        
    Returns:
        str: Valid interface name
        
    Raises:
        argparse.ArgumentTypeError: If interface is invalid
    """
    if not utils.valid_interface(value):
        raise argparse.ArgumentTypeError(f"A Valid Interface must be provided \n Use one of the following {utils.interfaces()}")
    return value

def is_valid_ip(value):
    """Validate that the provided string is a valid IPv4 address.
    
    Args:
        value: IP address string to validate
        
    Returns:
        str: Valid IP address
        
    Raises:
        argparse.ArgumentTypeError: If IP address is invalid
    """
    if utils.valid_ip(value):
        return str(value)
    else:
        raise argparse.ArgumentTypeError(f"'{value}' is not a valid IPv4 address")

def rogue_dhcp_action(args):
    """Action handler for rogue-dhcp command.
    
    Sets up and starts a rogue DHCP server with the provided or default configuration.
    
    Args:
        args: Parsed command-line arguments containing interface, server, router, and offer IP
    """
    # Check for root privileges before attempting to bind to port 67
    if not check_root_privileges():
        print(Fore.RED + "[X] - " + Style.BRIGHT + "Root privileges required!" + Style.RESET_ALL)
        print(Fore.YELLOW + "[!] - " + Style.BRIGHT + "DHCP servers must bind to port 67, which requires root/administrator privileges." + Style.RESET_ALL)
        print(Fore.CYAN + "[i] - " + Style.BRIGHT + "Please run with sudo: sudo python3 dhcptoolset.py rogue-dhcp -i " + args.iface + Style.RESET_ALL)
        print(Fore.CYAN + "[i] - " + Style.BRIGHT + "Or: sudo dhcptoolset rogue-dhcp -i " + args.iface + Style.RESET_ALL)
        sys.exit(1)
    
    network_info = utils.get_main_network_info()
    if args.server is None:
        args.server = utils.get_default_gateway(args.iface)
    if args.router is None:
        args.router = utils.get_default_gateway(args.iface)
    if args.offer is None:
        args.offer = utils.generate_random_ip(network_info['Interface'])
    console = Console()
    table = Table(title=f"DHCP Server Info", box=box.ROUNDED, show_header=True)
    table.add_column("Field", justify="left", style="cyan", no_wrap=True)
    table.add_column("Value", justify="center", style="bold green")
    fields = [
            ("Network", args.server),
            ("Default Gateway", args.router),
            ("Client IP", args.offer)
        ]
    for field, range_ in fields:
        table.add_row(field, range_)
    console.print(table)
    rogue_server = DHCP_server(args)
    try:
        rogue_server.start_server()
        rogue_server.server_broadcast(args)
    except PortInUseError:
        # Port conflict - already handled with nice messages, exit cleanly
        sys.exit(1)

parser = argparse.ArgumentParser(description="DHCP Toolset")
subparsers = parser.add_subparsers(help='Type of script')
dhcp_server_parser = subparsers.add_parser('rogue-dhcp', help='Deploy Rogue DHCP')
dhcp_server_parser.set_defaults(func=rogue_dhcp_action)
dhcp_server_parser.add_argument('-i', '--iface', help = 'Network interface to listen', required = True, type=is_valid_interface)
dhcp_server_parser.add_argument('-s', '--server', help = 'DHCP Server', required = False, type=is_valid_ip)
dhcp_server_parser.add_argument('-r', '--router', help = 'Default Gateway IP', required = False, type=is_valid_ip)
dhcp_server_parser.add_argument('-o', '--offer', help = 'IP to offer to Clients. Leave blank to random ip', type=is_valid_ip)

def fake_client_action(args):
    """Action handler for fake-client command.
    
    Placeholder for future implementation of fake DHCP client functionality.
    
    Args:
        args: Parsed command-line arguments containing interface information
    """
    print(Fore.YELLOW + "[!] - " + Style.BRIGHT + "Fake-client functionality is not yet implemented." + Style.RESET_ALL)
    print(Fore.CYAN + "[i] - " + Style.BRIGHT + "This feature will allow sending fake DHCP requests to the network." + Style.RESET_ALL)

dhcp_client_parser = subparsers.add_parser('fake-client', help='Send fake DHCP requests to the network')
dhcp_client_parser.set_defaults(func=fake_client_action)
dhcp_client_parser.add_argument('-i', '--iface', help='Network interface to use', required=True, type=is_valid_interface)

def main():
    """Main entry point for DHCP Toolset."""
    if len(sys.argv) == 1:
        parser.print_help()
    else:
        try:
            args = parser.parse_args()
            if hasattr(args, 'func'):
                args.func(args)
            else:
                parser.print_help()
        except argparse.ArgumentTypeError as e:
            print(Fore.RED + "[X] - " + Style.BRIGHT + f"An error has occurred: {e}" + Style.RESET_ALL)
            sys.exit(1)
        except KeyboardInterrupt:
            print(Fore.RED + "\n[X] - " + Style.BRIGHT + "Execution interrupted" + Style.RESET_ALL)
            sys.exit(0)
        except AttributeError:
            parser.print_help()
            sys.exit(1)

if __name__ == '__main__':
    main()

