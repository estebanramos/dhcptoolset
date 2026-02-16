import netifaces as ni
import socket, ipaddress, random, requests

def decode_hexstring_offer_options(options_data):
    dhcp_offer = options_data[0:3]
    subnet_mask = options_data[3:9]
    router = options_data[9:15]
    lease_time = options_data[15:21]
    dhcp_server = options_data[21:27]
    dns_data = options_data[27:]
    return('.'.join(str(b) for b in dns_data[2::]))


def get_main_network_info():
    # Get the hostname of the server
    hostname = socket.gethostname()

    # Get the IP address associated with the server's hostname
    server_ip = socket.gethostbyname(hostname)

    # Get the default network interface (may need to be modified based on your setup)
    default_interface = ni.gateways()['default'][ni.AF_INET][1]

    # Get the network configuration for the default interface
    interface_info = ni.ifaddresses(default_interface)

    
    # Extract the network address and netmask from the interface configuration
    if ni.AF_INET in interface_info:
        interface_ipv4_info = interface_info[ni.AF_INET][0]
        client_address = interface_ipv4_info['addr']
        netmask = interface_ipv4_info['netmask']
        network = ipaddress.IPv4Network(f"{client_address}/{netmask}", strict=False)
        network_address = f"{network.network_address}/{network.prefixlen}"
        return {
            'Interface': default_interface,
            'Client Address': client_address,
            'Netmask': netmask,
            'Gateway': get_default_gateway(default_interface),
            'Network': network_address
        }
    else:
        return None  # No IPv4 configuration found for the default interface
    
def valid_interface(iface):
    """Check if a network interface exists on the system.
    
    Args:
        iface: Interface name to check
        
    Returns:
        bool: True if interface exists, False otherwise
    """
    return iface in ni.interfaces()

def interfaces():
    """Get list of all available network interfaces.
    
    Returns:
        list: List of interface names
    """
    return ni.interfaces()

def valid_ip(ip):
    """Validate if a string is a valid IPv4 address.
    
    Args:
        ip: IP address string to validate
        
    Returns:
        bool: True if valid IPv4 address, False otherwise
    """
    try:
        socket.inet_aton(ip)
        return True
    except (socket.error, OSError):
        return False

def ip_network(ip, iface):
    an_address = ipaddress.ip_address(ip)
    a_network = ipaddress.ip_network('192.168.0.0/24')

    return an_address in a_network

def get_default_gateway(interface):
    gateways = ni.gateways()[2]
    for gw in gateways:
        if gw[1] == interface:
            return gw[0]
        
def get_network_address(ifname):
    addresses = ni.ifaddresses(ifname)
    ip_info = addresses[ni.AF_INET][0]
    ip_addr = ip_info['addr']
    netmask = ip_info['netmask']

    network = ipaddress.IPv4Network(f'{ip_addr}/{netmask}', strict=False)
    return network

def generate_random_ip(iface):
    network = get_network_address(iface)
    network_hosts = list(network.hosts())
    random_ip = random.choice(network_hosts)
    return str(random_ip)

def get_vendor(mac_address):
    url = f"https://api.macvendors.com/{mac_address}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.text
        else:
            return "Couldn't find MAC Vendor"
    except Exception as e:
        return f"Error: {str(e)}"