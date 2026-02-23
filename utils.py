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
    

def get_interface_ipv4_info(iface: str):
    """Get IPv4 info for a specific interface.

    Returns:
        dict with keys: Interface, Client Address, Netmask, Gateway, Network
        or None if the interface has no IPv4 config.
    """
    interface_info = ni.ifaddresses(iface)
    if ni.AF_INET not in interface_info:
        return None
    interface_ipv4_info = interface_info[ni.AF_INET][0]
    client_address = interface_ipv4_info["addr"]
    netmask = interface_ipv4_info["netmask"]
    network = ipaddress.IPv4Network(f"{client_address}/{netmask}", strict=False)
    network_address = f"{network.network_address}/{network.prefixlen}"
    return {
        "Interface": iface,
        "Client Address": client_address,
        "Netmask": netmask,
        "Gateway": get_default_gateway(iface),
        "Network": network_address,
    }
    
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


def get_mac_bytes(iface: str) -> bytes:
    """Get the MAC address of an interface as 6 raw bytes."""
    addresses = ni.ifaddresses(iface)
    link = addresses.get(ni.AF_LINK)
    if not link:
        raise RuntimeError(f"No MAC address found for interface {iface}")
    mac_str = link[0]["addr"]  # e.g. "aa:bb:cc:dd:ee:ff"
    return bytes(int(part, 16) for part in mac_str.split(":"))

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


# --- Offline heuristic device fingerprinting ---------------------------------

_OUI_DEVICE_MAP = {
    # These are just a few common examples; this mapping is heuristic, not exact.
    # Format: "AA:BB:CC": "Device category"
    "AC:CF:23": "Android phone/tablet (Samsung)",
    "60:21:C0": "Android phone/tablet (Samsung)",
    "F8:27:93": "Android phone/tablet (Xiaomi)",
    "FC:64:BA": "Android phone/tablet (Huawei/Honor)",
    "D8:9E:F3": "Android phone/tablet (Motorola/Lenovo)",
    "FC:FB:FB": "Apple device (iPhone/iPad/Mac)",
    "BC:92:6B": "Apple device (iPhone/iPad/Mac)",
    "10:40:F3": "Apple device (iPhone/iPad/Mac)",
    "00:1A:79": "Router / AP (TP-Link)",
    "F4:F5:D8": "Router / AP (Ubiquiti)",
    "00:24:D7": "Router / AP (Cisco/Linksys)",
    "B0:99:D7:": "Samsung Electronics Co.,Ltd",
    "5C-0C-E6": "Nintendo Co.,Ltd"
}


def _mac_to_oui(mac: str) -> str:
    """Normalize MAC string and return its OUI (first 3 octets) in AA:BB:CC form."""
    mac = mac.replace("-", ":").upper()
    parts = mac.split(":")
    if len(parts) < 3:
        return ""
    return ":".join(parts[:3])


def guess_device_type(mac: str, fingerprint: str | None = None) -> str:
    """Best-effort guess of device type based on MAC and optional fingerprint string.

    Args:
        mac: MAC address string like 'AA-BB-CC-DD-EE-FF' or 'AA:BB:CC:DD:EE:FF'
        fingerprint: Optional extra hint, e.g. DHCP vendor class ('android-dhcp-16'),
                     hostname, or vendor name.

    Returns:
        A short human-readable category like 'Android phone/tablet', 'Apple device', etc.,
        or 'Unknown device' if no heuristic matches.
    """
    oui = _mac_to_oui(mac)
    if oui in _OUI_DEVICE_MAP:
        return _OUI_DEVICE_MAP[oui]

    if fingerprint:
        f = fingerprint.lower()
        if "android" in f:
            return "Android device"
        if "iphone" in f or "ipad" in f or "ios" in f:
            return "Apple iOS device"
        if "mac" in f or "macbook" in f or "imac" in f:
            return "Apple macOS device"
        if "windows" in f or "msft" in f:
            return "Windows device"
        if "roku" in f:
            return "Roku / streaming device"
        if "sonos" in f:
            return "Sonos speaker"
        if "playstation" in f or "ps4" in f or "ps5" in f:
            return "Sony PlayStation"
        if "xbox" in f:
            return "Microsoft Xbox"
        if "smart-tv" in f or "tv" in f:
            return "Smart TV"

    return "Unknown device"