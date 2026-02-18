import socket
import subprocess
import os
import platform
from utils import decode_hexstring_offer_options
from model import DHCPMODEL, DHCPOFFER, DHCPREQUEST, DHCPPACK, DHCPDISCOVER
from rich.console import Console
from colorama import Fore, Back, Style, init as colorama_init


MAX_BYTES = 1024
serverPort = 67
colorama_init()

class PortInUseError(Exception):
    """Custom exception for port conflicts - suppresses traceback."""

    pass

def get_process_using_port(port):
    """Find the process name and PID using the specified port.
    
    Args:
        port: Port number to check
        
    Returns:
        tuple: (process_name, pid) or (None, None) if not found
    """
    system = platform.system().lower()
    
    try:
        if system == 'linux':
            # Try lsof first (most reliable)
            try:
                result = subprocess.run(
                    ['lsof', '-i', f'UDP:{port}'],
                    capture_output=True,
                    text=True,
                    timeout=2
                )
                if result.returncode == 0 and result.stdout:
                    lines = result.stdout.strip().split('\n')
                    if len(lines) > 1:  # Skip header
                        parts = lines[1].split()
                        if len(parts) >= 2:
                            process_name = parts[0]
                            pid = parts[1]
                            return (process_name, pid)
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass
            
            # Try fuser as fallback
            try:
                result = subprocess.run(
                    ['fuser', f'{port}/udp'],
                    capture_output=True,
                    text=True,
                    timeout=2
                )
                if result.returncode == 0 and result.stdout:
                    pid = result.stdout.strip().split()[0]
                    # Get process name from /proc
                    try:
                        with open(f'/proc/{pid}/comm', 'r') as f:
                            process_name = f.read().strip()
                        return (process_name, pid)
                    except (FileNotFoundError, PermissionError):
                        return (None, pid)
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass
            
            # Try netstat as last resort
            try:
                result = subprocess.run(
                    ['netstat', '-tulpn'],
                    capture_output=True,
                    text=True,
                    timeout=2
                )
                if result.returncode == 0:
                    for line in result.stdout.split('\n'):
                        if f':{port}' in line and 'udp' in line.lower():
                            parts = line.split()
                            if len(parts) >= 7:
                                pid_proc = parts[-1].split('/')
                                if len(pid_proc) == 2:
                                    process_name = pid_proc[0]
                                    pid = pid_proc[1]
                                    return (process_name, pid)
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass
                
        elif system == 'darwin':  # macOS
            try:
                result = subprocess.run(
                    ['lsof', '-i', f'UDP:{port}'],
                    capture_output=True,
                    text=True,
                    timeout=2
                )
                if result.returncode == 0 and result.stdout:
                    lines = result.stdout.strip().split('\n')
                    if len(lines) > 1:
                        parts = lines[1].split()
                        if len(parts) >= 2:
                            process_name = parts[0]
                            pid = parts[1]
                            return (process_name, pid)
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass
                
    except Exception:
        # Silently fail if we can't determine the process
        pass
    
    return (None, None)


def get_dhcp_message_type(dhcp_data: bytes) -> int:
    """Extract DHCP message type (option 53) from a raw DHCP packet.

    Returns:
        int: DHCP message type code (1=Discover, 2=Offer, 3=Request, ...), or 0 if unknown.
    """
    # Options start at byte 240
    options = dhcp_data[240:]
    i = 0
    while i < len(options):
        code = options[i]
        if code == 255:  # End option
            break
        if i + 1 >= len(options):
            break
        length = options[i + 1]
        if i + 2 + length > len(options):
            break
        if code == 53 and length >= 1:  # DHCP Message Type
            return options[i + 2]
        i += 2 + length
    return 0

class DHCP_server(object):
    """DHCP Server implementation for handling DHCP discovery and request packets."""

    def __init__(self, args):
        """Initialize DHCP server with configuration arguments.
        
        Args:
            args: Configuration arguments containing server, router, and offer IP settings
        """
        self.DHCPPACKET = DHCPDISCOVER()
        self.serverPort = 67
        self.args = args

    def start_server(self):
        """Start the DHCP server by binding to port 67.
        
        Raises:
            OSError: If the port is already in use or binding fails
            PermissionError: If root privileges are not available (should be caught earlier)
        """
        try:
            print(Fore.GREEN + "[#] - " + Style.BRIGHT + "DHCP server is starting..." + Style.RESET_ALL)
            self.s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
            self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            # Bind socket to specific interface to ensure packets only use that NIC
            self.s.setsockopt(socket.SOL_SOCKET, socket.SO_BINDTODEVICE, self.args.iface.encode())
            print(
                Fore.CYAN
                + "[i] - "
                + Style.BRIGHT
                + f"Socket bound to interface {self.args.iface} using SO_BINDTODEVICE"
                + Style.RESET_ALL
            )
            self.s.bind(("0.0.0.0", self.serverPort))
        except PermissionError as e:
            print(Fore.RED + "[X] - " + Style.BRIGHT + f"Permission denied: cannot bind to port {self.serverPort}" + Style.RESET_ALL)
            print(Fore.YELLOW + "[!] - " + Style.BRIGHT + "Port 67 is a privileged port and requires root/administrator privileges." + Style.RESET_ALL)
            print(Fore.CYAN + "[i] - " + Style.BRIGHT + "Please run with sudo or as administrator." + Style.RESET_ALL)
            # This should have been caught earlier by check_root_privileges, but just in case
            raise SystemExit(1)
        except OSError as e:
            if "Address already in use" in str(e) or e.errno == 98:  # EADDRINUSE
                print(Fore.RED + "[X] - " + Style.BRIGHT + f"Server port {self.serverPort} already in use" + Style.RESET_ALL)
                
                # Try to identify the process using the port
                process_name, pid = get_process_using_port(self.serverPort)
                if process_name and pid:
                    print(Fore.YELLOW + "[!] - " + Style.BRIGHT + f"Process '{process_name}' (PID: {pid}) is using port {self.serverPort}" + Style.RESET_ALL)
                    print(Fore.CYAN + "[i] - " + Style.BRIGHT + f"To stop it, run: sudo kill {pid}" + Style.RESET_ALL)
                    print(Fore.CYAN + "[i] - " + Style.BRIGHT + f"Or if it's a service: sudo systemctl stop {process_name}" + Style.RESET_ALL)
                else:
                    print(Fore.YELLOW + "[!] - " + Style.BRIGHT + "Another process is using port 67. Check with:" + Style.RESET_ALL)
                    print(Fore.CYAN + "[i] - " + Style.BRIGHT + "  sudo lsof -i UDP:67" + Style.RESET_ALL)
                    print(Fore.CYAN + "[i] - " + Style.BRIGHT + "  sudo netstat -tulpn | grep :67" + Style.RESET_ALL)
                # Raise custom exception that will be caught and handled without traceback
                raise PortInUseError()
            else:
                raise        

    def server_broadcast(self, args):
        """Handle a single DHCP cycle: one DISCOVER → OFFER and optional REQUEST → ACK.

        After completing (or timing out) a cycle, the function returns.
        """
        console = Console()

        print(
            Fore.YELLOW
            + "[!] - "
            + Style.BRIGHT
            + "Waiting for a single DHCP cycle (DISCOVER / REQUEST)..."
            + Style.RESET_ALL
        )

        offer = None
        offer_key = None  # (xid_bytes, client_mac_6_bytes)
        discover_count = 0

        # 1) Esperar el primer DISCOVER válido
        while True:
            data, address = self.s.recvfrom(MAX_BYTES)
            msg_type = get_dhcp_message_type(data)
            if msg_type != 1:
                # Ignore anything that is not a DISCOVER
                continue

            discovery = DHCPDISCOVER()
            discovery.from_raw_data(data)
            xid = discovery.XID
            client_mac = discovery.CHADDR1 + discovery.CHADDR2[:2]
            offer_key = (xid, client_mac)
            discover_count = 1

            print(
                Fore.CYAN
                + "[✓] - "
                + Style.BRIGHT
                + f"DISCOVER (CLIENT → SERVER) de {'-'.join(f'{b:02X}' for b in client_mac)} "
                + f"XID={xid.hex()}"
                + Style.RESET_ALL
            )
            DHCPMODEL.print_table_data(discovery.dhcp_data)

            offer = DHCPOFFER(args)
            offer.set_xid(discovery.XID)
            offer.set_chaddr(discovery.CHADDR1, discovery.CHADDR2)

            print(
                Fore.BLUE
                + "[i] - "
                + Style.BRIGHT
                + "OFFER (SERVER → CLIENT) para "
                + "-".join(f"{b:02X}" for b in client_mac)
                + f" IP={'.'.join(str(b) for b in offer.YIADDR)}"
                + Style.RESET_ALL
            )
            DHCPMODEL.print_table_data(offer.dhcp_data)

            dest = ("255.255.255.255", address[1])
            self.s.sendto(offer.dhcp_data, dest)
            break

        # 2) Esperar opcionalmente un REQUEST correspondiente, con timeout
        xid, client_mac = offer_key
        self.s.settimeout(3.0)
        try:
            while True:
                data, address = self.s.recvfrom(MAX_BYTES)
                msg_type = get_dhcp_message_type(data)

                if msg_type == 1:
                # Repeated DISCOVERs from the same client/XID: ignore up to a limit
                    tmp = DHCPDISCOVER()
                    tmp.from_raw_data(data)
                    if tmp.XID == xid and (tmp.CHADDR1 + tmp.CHADDR2[:2]) == client_mac:
                        discover_count += 1
                        if discover_count <= 3:
                            print(
                                Fore.YELLOW
                                + "[!] - "
                                + Style.BRIGHT
                                + "Repeated DISCOVER from the same client in a single cycle, ignoring."
                                + Style.RESET_ALL
                            )
                        if discover_count >= 5:
                            print(
                                Fore.YELLOW
                                + "[!] - "
                                + Style.BRIGHT
                                + "Too many DISCOVER messages without a REQUEST. Ending cycle."
                                + Style.RESET_ALL
                            )
                            break
                        continue
                    else:
                        # DISCOVER from another client: ignore in single-cycle mode
                        continue

                if msg_type == 3:
                    request_data = DHCPREQUEST()
                    request_data.from_raw_data(data)
                    if request_data.XID != xid or (
                        request_data.CHADDR1 + request_data.CHADDR2[:2]
                    ) != client_mac:
                        print(
                            Fore.YELLOW
                            + "[!] - "
                            + Style.BRIGHT
                            + "REQUEST received from another client/XID while in single-cycle mode. Ignoring."
                            + Style.RESET_ALL
                        )
                        continue

                    print(
                        Fore.CYAN
                        + "[✓] - "
                        + Style.BRIGHT
                        + f"REQUEST (CLIENT → SERVER) from {'-'.join(f'{b:02X}' for b in client_mac)} "
                        + f"XID={xid.hex()}"
                        + Style.RESET_ALL
                    )
                    DHCPMODEL.print_table_data(request_data.dhcp_data)

                    ack = DHCPPACK(offer)
                    ack.set_xid(request_data.XID)
                    ack.set_chaddr(request_data.CHADDR1, request_data.CHADDR2)

                    print(
                        Fore.BLUE
                        + "[i] - "
                        + Style.BRIGHT
                        + f"ACK (SERVER → CLIENT) for {'-'.join(f'{b:02X}' for b in client_mac)} "
                        + f"IP={'.'.join(str(b) for b in ack.YIADDR)}"
                        + Style.RESET_ALL
                    )
                    DHCPMODEL.print_table_data(ack.dhcp_data)

                    dest = ("255.255.255.255", address[1])
                    self.s.sendto(ack.dhcp_data, dest)

                    print(
                        Fore.GREEN
                        + "[✓] - "
                        + Style.BRIGHT
                        + f"Full DHCP cycle completed for {'-'.join(f'{b:02X}' for b in client_mac)} "
                        + f"→ {'.'.join(str(b) for b in ack.YIADDR)}"
                        + Style.RESET_ALL
                    )
                    break

                # Otros tipos: ignorar
                continue
        except KeyboardInterrupt:
            print(
                Fore.YELLOW
                + "\n[!] - "
                + Style.BRIGHT
                + "Server shutdown requested by user"
                + Style.RESET_ALL
            )
        except Exception as e:
                print(
                    Fore.RED
                    + "[X] - "
                    + Style.BRIGHT
                    + f"Error in DHCP cycle: {e}"
                    + Style.RESET_ALL
                )
        finally:
            # Quitar timeout y terminar la función (un solo ciclo)
            try:
                self.s.settimeout(None)
            except Exception:
                pass

if __name__ == '__main__':
    dhcp_server = DHCP_server()
    dhcp_server.server_broadcast()
