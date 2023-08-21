def decode_hexstring_offer_options(options_data):
    dhcp_offer = options_data[0:3]
    subnet_mask = options_data[3:9]
    router = options_data[9:15]
    lease_time = options_data[15:21]
    dhcp_server = options_data[21:27]
    dns_data = options_data[27:]
    return('.'.join(str(b) for b in dns_data[2::]))