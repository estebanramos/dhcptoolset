import argparse, utils, sys
import os
import socket
import struct
import random
import time
from dhcp_server import DHCP_server, PortInUseError, get_dhcp_message_type
from dhcp_fake_client import run_fake_client, run_fake_client_sniffer
from rich.console import Console
from rich.table import Table
from rich.live import Live
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
dhcp_server_parser.add_argument('--detect-device', action='store_true', help='Detect device vendor/type from MAC address using online API', required=False)


def fake_client_action(args):
    """Thin argparse wrapper for the fake DHCP client implementation."""
    vendor_class = getattr(args, "vendor_class", None)
    run_fake_client(args.iface, vendor_class)

dhcp_client_parser = subparsers.add_parser('fake-client', help='Send fake DHCP requests to the network')
dhcp_client_parser.set_defaults(func=fake_client_action)
dhcp_client_parser.add_argument('-i', '--iface', help='Network interface to use', required=True, type=is_valid_interface)
dhcp_client_parser.add_argument(
    '--vendor-class',
    help='Optional DHCP vendor class (option 60) to send in the fake DISCOVER. If omitted, a realistic-looking default is chosen.',
    required=False,
)


def fake_client_sniffer_action(args):
    """Fake DHCP client that sniffs responses at link layer (AF_PACKET)."""
    vendor_class = getattr(args, "vendor_class", None)
    run_fake_client_sniffer(args.iface, vendor_class)


dhcp_client_sniffer_parser = subparsers.add_parser(
    'fake-client-sniffer',
    help='Send fake DHCP DISCOVER and sniff DHCP responses at link layer (no UDP 68 bind needed)',
)
dhcp_client_sniffer_parser.set_defaults(func=fake_client_sniffer_action)
dhcp_client_sniffer_parser.add_argument(
    '-i', '--iface', help='Network interface to use', required=True, type=is_valid_interface
)
dhcp_client_sniffer_parser.add_argument(
    '--vendor-class',
    help='Optional DHCP vendor class (option 60) to send in the fake DISCOVER. If omitted, a realistic-looking default is chosen.',
    required=False,
)


def passive_listen_action(args):
    """Passively listen for DHCP clients on the network without responding.

    Shows a live-updating table of discovered devices.
    """
    if not check_root_privileges():
        print(
            Fore.RED
            + "[X] - "
            + Style.BRIGHT
            + "Root privileges required to listen on DHCP server port 67."
            + Style.RESET_ALL
        )
        print(
            Fore.CYAN
            + "[i] - "
            + Style.BRIGHT
            + f"Please run with sudo: sudo python3 dhcptoolset.py listen -i {args.iface}"
            + Style.RESET_ALL
        )
        sys.exit(1)

    console = Console()
    print(
        Fore.GREEN
        + "[#] - "
        + Style.BRIGHT
        + f"Starting passive DHCP listener on interface {args.iface} (no responses will be sent)..."
        + Style.RESET_ALL
    )

    # Create a UDP socket bound to DHCP server port 67 on the given interface
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    try:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        # Bind to specific interface so we only capture traffic on that NIC
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BINDTODEVICE, args.iface.encode())
        s.bind(("0.0.0.0", 67))
    except PermissionError:
        print(
            Fore.RED
            + "[X] - "
            + Style.BRIGHT
            + "Permission denied while binding passive listener to port 67."
            + Style.RESET_ALL
        )
        sys.exit(1)
    except OSError as e:
        print(
            Fore.RED
            + "[X] - "
            + Style.BRIGHT
            + f"Could not bind passive listener socket: {e}"
            + Style.RESET_ALL
        )
        sys.exit(1)

    s.settimeout(1.0)

    # Track seen clients by MAC
    clients = {}

    def build_table():
        table = Table(
            title="Passive DHCP Clients (listen-only)",
            box=box.ROUNDED,
            show_header=True,
        )
        table.add_column("MAC", style="cyan", no_wrap=True)
        table.add_column("Device Type", style="bright_cyan")
        table.add_column("Hostname", style="green")
        table.add_column("Vendor Class", style="magenta")
        table.add_column("Message Types", style="yellow")
        table.add_column("First Seen", style="white")
        table.add_column("Last Seen", style="white")
        table.add_column("Packets", style="blue")

        for mac, info in sorted(clients.items()):
            table.add_row(
                mac,
                info.get("device_type") or "-",
                info.get("hostname") or "-",
                info.get("vendor_class") or "-",
                ", ".join(sorted(info.get("msg_types", set()))) or "-",
                info.get("first_seen") or "-",
                info.get("last_seen") or "-",
                str(info.get("count", 0)),
            )
        return table

    def parse_client_info(data: bytes):
        # Basic BOOTP/DHCP header parsing
        if len(data) < 240:
            return None

        xid = data[4:8].hex().upper()
        ciaddr = ".".join(str(b) for b in data[12:16])
        yiaddr = ".".join(str(b) for b in data[16:20])
        chaddr = data[28:28 + 16]
        mac_bytes = chaddr[:6]
        mac_str = "-".join(f"{b:02X}" for b in mac_bytes)

        msg_type_code = get_dhcp_message_type(data)
        msg_type_map = {
            1: "DISCOVER",
            2: "OFFER",
            3: "REQUEST",
            4: "DECLINE",
            5: "ACK",
            6: "NAK",
            7: "RELEASE",
            8: "INFORM",
        }
        msg_type = msg_type_map.get(msg_type_code, f"TYPE-{msg_type_code}")

        hostname = ""
        vendor_class = ""

        # Parse options for hostname (12) and vendor class (60)
        options = data[240:]
        i = 0
        while i < len(options):
            code = options[i]
            if code == 255:  # End
                break
            if i + 1 >= len(options):
                break
            length = options[i + 1]
            if i + 2 + length > len(options):
                break
            value = options[i + 2 : i + 2 + length]

            if code == 12:  # Hostname
                try:
                    hostname = value.decode("utf-8", errors="ignore")
                except Exception:
                    hostname = ""
            elif code == 60:  # Vendor class identifier
                try:
                    vendor_class = value.decode("utf-8", errors="ignore")
                except Exception:
                    vendor_class = ""

            i += 2 + length

        return {
            "mac": mac_str,
            "xid": xid,
            "ciaddr": ciaddr,
            "yiaddr": yiaddr,
            "msg_type": msg_type,
            "hostname": hostname,
            "vendor_class": vendor_class,
        }

    with Live(build_table(), console=console, refresh_per_second=2) as live:
        try:
            while True:
                try:
                    data, addr = s.recvfrom(1024)
                except socket.timeout:
                    continue

                info = parse_client_info(data)
                if not info:
                    continue

                # Only care about client-originated messages (DISCOVER/REQUEST/INFORM/RELEASE)
                if info["msg_type"] not in ("DISCOVER", "REQUEST", "INFORM", "RELEASE"):
                    continue

                now = time.strftime("%H:%M:%S")
                mac = info["mac"]
                entry = clients.get(mac)
                if not entry:
                    device_type = utils.guess_device_type(
                        mac, info.get("vendor_class") or info.get("hostname")
                    )
                    clients[mac] = {
                        "device_type": device_type,
                        "hostname": info["hostname"],
                        "vendor_class": info["vendor_class"],
                        "msg_types": {info["msg_type"]},
                        "first_seen": now,
                        "last_seen": now,
                        "count": 1,
                    }
                else:
                    # Recompute device type if we gain more fingerprint info
                    fingerprint_hint = (
                        info.get("vendor_class")
                        or info.get("hostname")
                        or entry.get("vendor_class")
                        or entry.get("hostname")
                    )
                    entry["device_type"] = utils.guess_device_type(mac, fingerprint_hint)
                    entry["hostname"] = info["hostname"] or entry.get("hostname") or ""
                    entry["vendor_class"] = info["vendor_class"] or entry.get("vendor_class") or ""
                    entry.setdefault("msg_types", set()).add(info["msg_type"])
                    entry["last_seen"] = now
                    entry["count"] = entry.get("count", 0) + 1

                # Refresh live table with updated client list
                live.update(build_table())

        except KeyboardInterrupt:
            print(
                Fore.YELLOW
                + "\n[!] - "
                + Style.BRIGHT
                + "Passive DHCP listener stopped by user."
                + Style.RESET_ALL
            )
        finally:
            s.close()

dhcp_listen_parser = subparsers.add_parser(
    "listener", help="Passively listen for DHCP clients (no responses, live table)"
)
dhcp_listen_parser.set_defaults(func=passive_listen_action)
dhcp_listen_parser.add_argument(
    "-i", "--iface", help="Network interface to listen on", required=True, type=is_valid_interface
)

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

