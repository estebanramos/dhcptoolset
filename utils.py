import socket
import netifaces as ni
import ipaddress

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
        network_address = interface_ipv4_info['addr']
        netmask = interface_ipv4_info['netmask']

        return {
            'Interface': default_interface,
            'Network Address': network_address,
            'Netmask': netmask,
            'Gateway': ni.gateways()['default'][0]
        }
    else:
        return None  # No IPv4 configuration found for the default interface
    
def valid_interface(iface):
    return iface in ni.interfaces()

def valid_ip(ip):
    try:
        socket.inet_aton(ip)
        return True
    except:
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
    