import utils

class DHCPMODEL:
    def __init__(self, *args):
        pass

    
    def __getitem__(self, index):
        out = self._data[index]
        return (out)

    def __len__(self):
        return len(self._data)


    def set_xid(self, value):
         self.XID = value
         self.dhcp_data = self.OP + self.HTYPE + self.HLEN + self.HOPS + self.XID + self.SECS + self.FLAGS + self.CIADDR + self.YIADDR + self.SIADDR + self.GIADDR + self.CHADDR1 + self.CHADDR2 + self.CHADDR3 + self.CHADDR4 + self.CHADDR5 + self.Magiccookie + self.DHCPOptions1 + self.DHCPOptions2 + self.DHCPOptions3 + self.DHCPOptions4 + self.DHCPOptions5 + self.DHCPOptions6


    def set_chaddr(self, value, value2):
         self.CHADDR1 = value
         self.CHADDR2= value2
         self.dhcp_data = self.OP + self.HTYPE + self.HLEN + self.HOPS + self.XID + self.SECS + self.FLAGS + self.CIADDR + self.YIADDR + self.SIADDR + self.GIADDR + self.CHADDR1 + self.CHADDR2 + self.CHADDR3 + self.CHADDR4 + self.CHADDR5 + self.Magiccookie + self.DHCPOptions1 + self.DHCPOptions2 + self.DHCPOptions3 + self.DHCPOptions4 + self.DHCPOptions5 + self.DHCPOptions6


    def from_raw_data(self,dhcp_data):
            self.OP = bytes([dhcp_data[0]])
            self.HTYPE = bytes([dhcp_data[1]])
        # Parse Hardware Address Length
            self.HLEN = bytes([dhcp_data[2]])
         # Parse Hops
            self.HOPS = bytes([dhcp_data[3]])
            # Parse Transaction ID
            self.XID = dhcp_data[4:8]
            # Parse Seconds Elapsed
            self.SECS = dhcp_data[8:10]
            # Parse Flags
            self.FLAGS = dhcp_data[10:12]
            # Parse Client IP Address
            self.CIADDR = dhcp_data[12:16]
            # Parse Your IP Address (Server IP)
            self.YIADDR = dhcp_data[16:20]
            # Parse Next Server IP Address (Gateway IP)
            self.SIADDR = dhcp_data[20:24]
            self.GIADDR = dhcp_data[24:28]
            # Parse Client Hardware Address (MAC Address)
            self.CHADDR1 = dhcp_data[28:32]
            self.CHADDR2 = dhcp_data[32:36]
            self.CHADDR3 = dhcp_data[36:40]
            self.CHADDR4 = dhcp_data[40:44]
            self.CHADDR5 = dhcp_data[44:236]
            self.Magiccookie = dhcp_data[236:240]
            self.DHCPOptions1 = dhcp_data[240:243]
            self.DHCPOptions2 = dhcp_data[243:248]
            self.DHCPOptions3 = dhcp_data[248:253]
            self.DHCPOptions4 = dhcp_data[253:258]
            self.DHCPOptions5 = dhcp_data[258:263]
            self.DHCPOptions6 = dhcp_data[263::]

            self.dhcp_data = self.OP + self.HTYPE + self.HLEN + self.HOPS + self.XID + self.SECS + self.FLAGS + self.CIADDR + self.YIADDR + self.SIADDR + self.GIADDR + self.CHADDR1 + self.CHADDR2 + self.CHADDR3 + self.CHADDR4 + self.CHADDR5 + self.Magiccookie + self.DHCPOptions1 + self.DHCPOptions2 + self.DHCPOptions3 + self.DHCPOptions4 + self.DHCPOptions5 + self.DHCPOptions6
  
  
    def print_data(self):
        # Write again
        print(f"Transaction ID: {''.join(f'{b:02X}' for b in self.XID)}")
        pass

    def print_raw_data(dhcp_data):
        # Parse Message Type (Op Code)
        message_type = dhcp_data[0]
        # Parse Hardware Type
        hardware_type = dhcp_data[1]
        # Parse Hardware Address Length
        hardware_addr_len = dhcp_data[2]
         # Parse Hops
        hops = dhcp_data[3]
            # Parse Transaction ID
        transaction_id = dhcp_data[4:8]
            # Parse Seconds Elapsed
        seconds_elapsed = dhcp_data[8:10]
            # Parse Flags
        flags = dhcp_data[10:12]
            # Parse Client IP Address
        client_ip = dhcp_data[12:16]
            # Parse Your IP Address (Server IP)
        server_ip = dhcp_data[16:20]
            # Parse Next Server IP Address (Gateway IP)
        gateway_ip = dhcp_data[20:24]
            # Parse Client Hardware Address (MAC Address)
        client_hw_addr = dhcp_data[28:34]
        # Parse Options (partial parsing)
        options = dhcp_data[240:]
        # Print Decoded Information
        print(f"Message Type: {message_type}")
        print(f"Hardware Type: {hardware_type}")
        print(f"Hardware Address Length: {hardware_addr_len}")
        print(f"Hops: {hops}")
        print(f"Transaction ID: {''.join(f'{b:02X}' for b in transaction_id)}")
        print(f"Seconds Elapsed: {int.from_bytes(seconds_elapsed, byteorder='big')}")
        print(f"Flags: {''.join(f'{b:02X}' for b in flags)}")
        print(f"Client IP Address: {'.'.join(str(b) for b in client_ip)}")
        print(f"Your IP Address (Server IP): {'.'.join(str(b) for b in server_ip)}")
        print(f"Next Server IP Address (Gateway IP): {'.'.join(str(b) for b in gateway_ip)}")
        print(f"Client Hardware Address (MAC Address): {'-'.join(f'{b:02X}' for b in client_hw_addr)}")
        print(f"Options (partial): {options}")
    
class DHCPDISCOVER(DHCPMODEL):
        def __init__(self):
            pass


class DHCPOFFER(DHCPMODEL):
        def __init__(self, args):
            DHCP_SERVER = bytes(int(octet) for octet in args.server.split('.'))
            ROUTER = bytes(int(octet) for octet in args.router.split('.'))
            OFFER = bytes(int(octet) for octet in args.offer.split('.'))
            self.OP = bytes([0x02])
            self.HTYPE = bytes([0x01])
            self.HLEN = bytes([0x06])
            self.HOPS = bytes([0x00])
            self.XID = bytes([0x39, 0x03, 0xF3, 0x26])
            self.SECS = bytes([0x00, 0x00])
            self.FLAGS = bytes([0x00, 0x00])
            self.CIADDR = bytes([0x00, 0x00, 0x00, 0x00])
            self.YIADDR = OFFER
            self.SIADDR = DHCP_SERVER
            self.GIADDR = ROUTER
            self.CHADDR1 = bytes([0xBC, 0x10, 0x7B, 0x69]) 
            self.CHADDR2 = bytes([0x1B, 0xC2, 0x00, 0x00])
            self.CHADDR3 = bytes([0x00, 0x00, 0x00, 0x00]) 
            self.CHADDR4 = bytes([0x00, 0x00, 0x00, 0x00]) 
            self.CHADDR5 = bytes(192)
            self.Magiccookie = bytes([0x63, 0x82, 0x53, 0x63])
            self.DHCPOptions1 = bytes([53 , 1 , 2]) # DHCP Offer
            self.DHCPOptions2 = bytes([1 , 4 , 0xFF, 0xFF, 0xFF, 0x00]) 
            self.DHCPOptions3 = bytes([3 , 4 , 0xC0, 0xA8, 0x01, 0x01]) 
            self.DHCPOptions4 = bytes([51 , 4 , 0x00, 0x01, 0x51, 0x80]) 
            self.DHCPOptions5 = bytes([54 , 4 , 0xC0, 0xA8, 0x01, 0x01])
            self.DHCPOptions6 = bytes([6 , 4 , 0x08, 0x08, 0x08, 0x08]) 
            self.dhcp_data = self.OP + self.HTYPE + self.HLEN + self.HOPS + self.XID + self.SECS + self.FLAGS + self.CIADDR + self.YIADDR + self.SIADDR + self.GIADDR + self.CHADDR1 + self.CHADDR2 + self.CHADDR3 + self.CHADDR4 + self.CHADDR5 + self.Magiccookie + self.DHCPOptions1 + self.DHCPOptions2 + self.DHCPOptions3 + self.DHCPOptions4 + self.DHCPOptions5


class DHCPREQUEST(DHCPMODEL):
    pass

class DHCPPACK(DHCPMODEL): 
        def __init__(self, dhcp_offer):
            self.__dict__.update(dhcp_offer.__dict__) 
            self.Magiccookie = bytes([0x63, 0x82, 0x53, 0x63])
            self.DHCPOptions1 = bytes([53 , 1 , 5]) # DHCP Offer
            self.DHCPOptions2 = bytes([1 , 4 , 0xFF, 0xFF, 0xFF, 0x00]) 
            self.DHCPOptions3 = bytes([3 , 4 , 0xC0, 0xA8, 0x01, 0x01]) 
            self.DHCPOptions4 = bytes([51 , 4 , 0x00, 0x01, 0x51, 0x80]) 
            self.DHCPOptions5 = bytes([54 , 4 , 0xC0, 0xA8, 0x01, 0x01])
            self.DHCPOptions6 = bytes([6 , 4 , 0x08, 0x08, 0x08, 0x08])
            self.dhcp_data = self.OP + self.HTYPE + self.HLEN + self.HOPS + self.XID + self.SECS + self.FLAGS + self.CIADDR + self.YIADDR + self.SIADDR + self.GIADDR + self.CHADDR1 + self.CHADDR2 + self.CHADDR3 + self.CHADDR4 + self.CHADDR5 + self.Magiccookie + self.DHCPOptions1 + self.DHCPOptions2 + self.DHCPOptions3 + self.DHCPOptions4 + self.DHCPOptions5