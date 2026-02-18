import argparse, utils, sys
import os
import socket
import struct
import random
import time
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


def parse_dns_list(value: str):
    """Parse a comma-separated list of IPv4 addresses for DNS."""
    dns_raw = [v.strip() for v in value.split(",")]
    dns_list = [v for v in dns_raw if v]
    if not dns_list:
        raise argparse.ArgumentTypeError("'--dns' must contain at least one IP")
    invalid = [ip for ip in dns_list if not utils.valid_ip(ip)]
    if invalid:
        raise argparse.ArgumentTypeError(f"Invalid DNS IP(s): {', '.join(invalid)}")
    return dns_list

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
    
    network_info = utils.get_interface_ipv4_info(args.iface)
    if network_info is None:
        print(Fore.RED + "[X] - " + Style.BRIGHT + f"No IPv4 configuration found for interface {args.iface}" + Style.RESET_ALL)
        sys.exit(1)

    # Critical correctness:
    # - DHCP Server Identifier (option 54) should be the DHCP server's IP (OUR interface IP).
    # - Router (option 3) is the default gateway we want clients to use.
    if args.server is None:
        args.server = network_info["Client Address"]
    if args.router is None:
        args.router = network_info["Gateway"]
    args.netmask = network_info["Netmask"]

    # DNS servers
    if getattr(args, "dns", None) is None:
        args.dns_list = [args.router] if args.router else []
    else:
        args.dns_list = parse_dns_list(args.dns)

    if args.offer is None:
        args.offer = utils.generate_random_ip(args.iface)
    console = Console()
    table = Table(title=f"DHCP Server Info", box=box.ROUNDED, show_header=True)
    table.add_column("Field", justify="left", style="cyan", no_wrap=True)
    table.add_column("Value", justify="center", style="bold green")
    fields = [
        ("Interface", args.iface),
        ("Network", network_info["Network"]),
        ("DHCP Server (this host)", args.server),
        ("Default Gateway", args.router),
        ("Client IP Offer", args.offer),
        ("DNS Servers", ", ".join(args.dns_list) if args.dns_list else "N/A"),
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
dhcp_server_parser.add_argument('--dns', help='Comma-separated DNS servers to offer to clients (default: router IP)', required=False)

def build_discover_packet(iface: str):
    """Build a minimal DHCP DISCOVER packet using the MAC of the given interface."""
    mac = utils.get_mac_bytes(iface)
    xid = random.getrandbits(32).to_bytes(4, byteorder="big")

    op = b"\x01"        # BOOTREQUEST
    htype = b"\x01"     # Ethernet
    hlen = b"\x06"      # MAC length
    hops = b"\x00"
    secs = b"\x00\x00"
    flags = b"\x00\x00"
    ciaddr = b"\x00\x00\x00\x00"
    yiaddr = b"\x00\x00\x00\x00"
    siaddr = b"\x00\x00\x00\x00"
    giaddr = b"\x00\x00\x00\x00"

    chaddr = mac + b"\x00" * (16 - len(mac))  # 16 bytes
    sname = b"\x00" * 64
    file_field = b"\x00" * 128
    magic_cookie = b"\x63\x82\x53\x63"

    # Options: DHCP Message Type (53=Discover), Parameter Request List (55), END (255)
    options = b""
    options += b"\x35\x01\x01"  # Option 53, len 1, DHCPDISCOVER
    options += b"\x37\x04\x01\x03\x06\x2a"  # Option 55: request 1,3,6,42 (just as example)
    options += b"\xff"  # END

    dhcp_packet = (
        op
        + htype
        + hlen
        + hops
        + xid
        + secs
        + flags
        + ciaddr
        + yiaddr
        + siaddr
        + giaddr
        + chaddr
        + sname
        + file_field
        + magic_cookie
        + options
    )
    return dhcp_packet, xid, mac


def fake_client_action(args):
    """Minimal fake DHCP client to discover active DHCP servers on the network."""

    if not check_root_privileges():
        print(
            Fore.RED
            + "[X] - "
            + Style.BRIGHT
            + "Root privileges required to send/receive DHCP packets (ports 67/68)."
            + Style.RESET_ALL
        )
        sys.exit(1)

    discover, xid, mac = build_discover_packet(args.iface)
    mac_str = "-".join(f"{b:02X}" for b in mac)

    print(
        Fore.CYAN
        + "[i] - "
        + Style.BRIGHT
        + f"Sending DHCP DISCOVER from {mac_str} on interface {args.iface}..."
        + Style.RESET_ALL
    )

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        # Muchos sistemas ya tienen un cliente DHCP escuchando en 68.
        # En lugar de bindear a 68, dejamos que el SO elija un puerto efímero.
        s.bind(("", 0))
    except PermissionError:
        print(
            Fore.RED
            + "[X] - "
            + Style.BRIGHT
            + "Could not create UDP socket for DHCP. Please run with sudo."
            + Style.RESET_ALL
        )
        sys.exit(1)

    local_port = s.getsockname()[1]

    # Enviamos DISCOVER desde nuestro puerto efímero hacia el puerto 67 del/los servidor(es)
    s.sendto(discover, ("255.255.255.255", 67))

    s.settimeout(3.0)
    seen_servers = set()

    start = time.time()
    while time.time() - start < 3.0:
        try:
            data, addr = s.recvfrom(1024)
        except socket.timeout:
            break

        src_ip, src_port = addr
        # Sólo nos interesan respuestas de servidores DHCP (src port 67)
        if src_port != 67:
            continue

        # Check XID matches
        if data[4:8] != xid:
            continue

        yiaddr = ".".join(str(b) for b in data[16:20])

        # Parse options to get message type and Server-ID
        options = data[240:]
        msg_type = None
        server_id = None
        i = 0
        while i < len(options):
            code = options[i]
            if code == 255:
                break
            if i + 1 >= len(options):
                break
            length = options[i + 1]
            if i + 2 + length > len(options):
                break
            value = options[i + 2 : i + 2 + length]
            if code == 53 and length >= 1:
                msg_type = value[0]
            if code == 54 and length == 4:
                server_id = ".".join(str(b) for b in value)
            i += 2 + length

        if msg_type not in (2, 5):  # Offer or ACK
            continue

        key = server_id or src_ip
        if key in seen_servers:
            continue
        seen_servers.add(key)

        tipo = "OFFER" if msg_type == 2 else "ACK"
        print(
            Fore.GREEN
            + "[✓] - "
            + Style.BRIGHT
            + f"Servidor DHCP detectado: {key} (src IP {src_ip}) → ofreció IP {yiaddr} ({tipo})"
            + Style.RESET_ALL
        )

    if not seen_servers:
        print(
            Fore.YELLOW
            + "[!] - "
            + Style.BRIGHT
            + "No se detectaron respuestas DHCP (OFFER/ACK) en la red."
            + Style.RESET_ALL
        )

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

