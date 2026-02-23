import os
import socket
import random
import time
import struct

from colorama import Fore, Style, init as colorama_init

import utils

colorama_init()


def check_root_privileges() -> bool:
    """Check if the script is running with root/administrator privileges."""
    return os.geteuid() == 0 if hasattr(os, "geteuid") else False


def build_discover_packet(iface: str = None, mac: bytes = None, hostname: str = None, vendor_class: str = None):
    """Build a minimal DHCP DISCOVER packet.

    If 'mac' is not provided, it will try to use the MAC of the given interface.
    If no interface is provided either, a random locally-administered MAC will be used.
    """
    if mac is None:
        if iface is not None:
            mac = utils.get_mac_bytes(iface)
        else:
            # Generate a random locally-administered unicast MAC (x2:x?:?:?:?:?)
            first = random.randint(0x00, 0xFF)
            first = (first | 0x02) & 0xFE  # set local bit, clear multicast bit
            mac = bytes([first]) + bytes(random.randint(0x00, 0xFF) for _ in range(5))

    if hostname is None:
        hostname = ""

    if vendor_class is None:
        vendor_class = ""

    xid = random.getrandbits(32).to_bytes(4, byteorder="big")

    op = b"\x01"  # BOOTREQUEST
    htype = b"\x01"  # Ethernet
    hlen = b"\x06"  # MAC length
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

    # Options: DHCP Message Type (53=Discover), optional Hostname (12),
    # optional Vendor Class (60), Parameter Request List (55), END (255)
    options = b""
    options += b"\x35\x01\x01"  # Option 53, len 1, DHCPDISCOVER

    if hostname:
        hostname_bytes = hostname.encode("utf-8", errors="ignore")[:63]
        options += bytes([12, len(hostname_bytes)]) + hostname_bytes  # Option 12: Hostname

    if vendor_class:
        vendor_class_bytes = vendor_class.encode("utf-8", errors="ignore")[:63]
        options += bytes([60, len(vendor_class_bytes)]) + vendor_class_bytes  # Option 60: Vendor class

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
    return dhcp_packet, xid, mac, vendor_class


def run_fake_client(iface: str, vendor_class: str | None = None):
    """Send a fake DHCP DISCOVER with a random MAC/hostname and print detected servers."""

    if not check_root_privileges():
        print(
            Fore.RED
            + "[X] - "
            + Style.BRIGHT
            + "Root privileges required to send/receive DHCP packets (ports 67/68)."
            + Style.RESET_ALL
        )
        raise SystemExit(1)

    # Generate a random fake MAC and hostname so the listener can detect them as new devices
    fake_mac = bytes([(random.randint(0, 255) | 0x02) & 0xFE]) + bytes(
        random.randint(0, 255) for _ in range(5)
    )
    fake_hostname = "FAKE-" + "".join(
        random.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789") for _ in range(8)
    )

    if vendor_class is None:
        # Pick a somewhat realistic-looking vendor class so it blends in
        vendor_class = random.choice(
            [
                "android-dhcp-16",
                "MSFT 5.0",
                "dhcptoolset-test",
            ]
        )

    discover, xid, _, _ = build_discover_packet(
        iface=iface, mac=fake_mac, hostname=fake_hostname, vendor_class=vendor_class
    )
    mac_str = "-".join(f"{b:02X}" for b in fake_mac)

    print(
        Fore.CYAN
        + "[i] - "
        + Style.BRIGHT
        + f"Sending DHCP DISCOVER from {mac_str} (hostname={fake_hostname}, vendor_class={vendor_class}) on interface {iface}..."
        + Style.RESET_ALL
    )

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        # Bind to the specific interface so the DISCOVER goes out through that NIC
        try:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_BINDTODEVICE, iface.encode())
        except OSError:
            # If SO_BINDTODEVICE is not supported or fails, continue anyway
            pass
        # Many systems already have a DHCP client bound to 68; use an ephemeral port instead.
        s.bind(("", 0))
    except PermissionError:
        print(
            Fore.RED
            + "[X] - "
            + Style.BRIGHT
            + "Could not create UDP socket for DHCP. Please run with sudo."
            + Style.RESET_ALL
        )
        raise SystemExit(1)

    # Send DISCOVER
    s.sendto(discover, ("255.255.255.255", 67))

    s.settimeout(3.0)
    seen_servers = set()

    start = time.time()
    try:
        while time.time() - start < 3.0:
            try:
                data, addr = s.recvfrom(1024)
            except socket.timeout:
                break

            src_ip, src_port = addr
            # Only care about responses from DHCP servers (src port 67)
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
                + f"Detected DHCP server: {key} (src IP {src_ip}) → offered IP {yiaddr} ({tipo})"
                + Style.RESET_ALL
            )

    finally:
        s.close()

    if not seen_servers:
        print(
            Fore.YELLOW
            + "[!] - "
            + Style.BRIGHT
            + "No DHCP responses (OFFER/ACK) detected on the network."
            + Style.RESET_ALL
        )


def run_fake_client_sniffer(iface: str, vendor_class: str | None = None):
    """Send a fake DHCP DISCOVER and sniff responses at link layer (AF_PACKET).

    This does NOT rely on binding to UDP port 68, so it can see replies even if
    the system DHCP client is already using that port.
    """

    if not check_root_privileges():
        print(
            Fore.RED
            + "[X] - "
            + Style.BRIGHT
            + "Root privileges required to send/receive raw DHCP packets."
            + Style.RESET_ALL
        )
        raise SystemExit(1)

    # Generate fake identity
    fake_mac = bytes([(random.randint(0, 255) | 0x02) & 0xFE]) + bytes(
        random.randint(0, 255) for _ in range(5)
    )
    fake_hostname = "FAKE-" + "".join(
        random.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789") for _ in range(8)
    )

    if vendor_class is None:
        vendor_class = random.choice(
            [
                "android-dhcp-16",
                "MSFT 5.0",
                "dhcptoolset-test",
            ]
        )

    discover, xid, _, _ = build_discover_packet(
        iface=iface, mac=fake_mac, hostname=fake_hostname, vendor_class=vendor_class
    )
    mac_str = "-".join(f"{b:02X}" for b in fake_mac)

    print(
        Fore.CYAN
        + "[i] - "
        + Style.BRIGHT
        + f"[sniffer] Sending DHCP DISCOVER from {mac_str} (hostname={fake_hostname}, vendor_class={vendor_class}) on interface {iface}..."
        + Style.RESET_ALL
    )

    # UDP socket just for sending the DISCOVER
    send_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        send_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        try:
            send_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BINDTODEVICE, iface.encode())
        except OSError:
            pass
        send_sock.bind(("", 0))
    except PermissionError:
        print(
            Fore.RED
            + "[X] - "
            + Style.BRIGHT
            + "Could not create UDP socket for DHCP. Please run with sudo."
            + Style.RESET_ALL
        )
        raise SystemExit(1)

    # Send DISCOVER
    send_sock.sendto(discover, ("255.255.255.255", 67))

    # Raw AF_PACKET socket to sniff replies on the interface
    sniff_sock = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.ntohs(0x0800))
    try:
        sniff_sock.bind((iface, 0))
    except OSError as e:
        print(
            Fore.RED
            + "[X] - "
            + Style.BRIGHT
            + f"Could not bind raw socket on {iface}: {e}"
            + Style.RESET_ALL
        )
        send_sock.close()
        raise SystemExit(1)

    sniff_sock.settimeout(3.0)
    seen_servers = set()
    start = time.time()

    try:
        while time.time() - start < 3.0:
            try:
                frame, addr = sniff_sock.recvfrom(65535)
            except socket.timeout:
                break

            if len(frame) < 14 + 20 + 8 + 240:
                continue

            # Ethernet header
            eth_type = struct.unpack("!H", frame[12:14])[0]
            if eth_type != 0x0800:  # Not IPv4
                continue

            # IP header
            ip_header = frame[14:34]
            ip_proto = ip_header[9]
            if ip_proto != 17:  # Not UDP
                continue
            ihl = (ip_header[0] & 0x0F) * 4
            src_ip = ".".join(str(b) for b in ip_header[12:16])

            # UDP header
            udp_offset = 14 + ihl
            udp_header = frame[udp_offset : udp_offset + 8]
            if len(udp_header) < 8:
                continue
            src_port, dst_port, udp_len, udp_checksum = struct.unpack("!HHHH", udp_header)

            # Replies from DHCP servers: src port 67 → dst port 68
            if src_port != 67 or dst_port != 68:
                continue

            # BOOTP/DHCP payload
            dhcp = frame[udp_offset + 8 :]
            if len(dhcp) < 240:
                continue

            # Match our XID and MAC so we only see responses to our fake client
            if dhcp[4:8] != xid:
                continue
            if dhcp[28:34] != fake_mac:
                continue

            yiaddr = ".".join(str(b) for b in dhcp[16:20])

            # Parse options to get message type and Server-ID
            options = dhcp[240:]
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
                + f"[sniffer] Detected DHCP server: {key} (src IP {src_ip}) → offered IP {yiaddr} ({tipo})"
                + Style.RESET_ALL
            )
    finally:
        sniff_sock.close()
        send_sock.close()

    if not seen_servers:
        print(
            Fore.YELLOW
            + "[!] - "
            + Style.BRIGHT
            + "[sniffer] No DHCP responses (OFFER/ACK) detected on the network."
            + Style.RESET_ALL
        )

