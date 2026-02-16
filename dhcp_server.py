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
            print(Fore.GREEN + "[#] - " + Style.BRIGHT + "DHCP Server is starting..." + Style.RESET_ALL)
            self.s=socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
            self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR,1)
            self.s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST,1)
            self.s.bind(('0.0.0.0', self.serverPort))
        except PermissionError as e:
            print(Fore.RED + "[X] - " + Style.BRIGHT + f"Permission denied: Cannot bind to port {self.serverPort}" + Style.RESET_ALL)
            print(Fore.YELLOW + "[!] - " + Style.BRIGHT + "Port 67 is a privileged port and requires root/administrator privileges." + Style.RESET_ALL)
            print(Fore.CYAN + "[i] - " + Style.BRIGHT + "Please run with sudo or as administrator." + Style.RESET_ALL)
            # This should have been caught earlier by check_root_privileges, but just in case
            raise SystemExit(1)
        except OSError as e:
            if 'Address already in use' in str(e) or e.errno == 98:  # EADDRINUSE
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
        """Main server loop to handle DHCP discovery and request packets."""
        running = True
        while running:
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
                    # Continue listening for more requests instead of breaking
                except KeyboardInterrupt:
                    print(Fore.YELLOW + "\n[!] - " + Style.BRIGHT + "Server shutdown requested" + Style.RESET_ALL)
                    running = False
                    break
                except Exception as e:
                    print(Fore.RED + "[X] - " + Style.BRIGHT + f"Error processing DHCP request: {e}" + Style.RESET_ALL)
                    # Continue listening for more requests
            except KeyboardInterrupt:
                print(Fore.YELLOW + "\n[!] - " + Style.BRIGHT + "Server shutdown requested" + Style.RESET_ALL)
                running = False
                break
            except Exception as e:
                print(Fore.RED + "[X] - " + Style.BRIGHT + f"Error receiving DHCP discovery: {e}" + Style.RESET_ALL)
                # Continue listening

if __name__ == '__main__':
    dhcp_server = DHCP_server()
    dhcp_server.server_broadcast()
