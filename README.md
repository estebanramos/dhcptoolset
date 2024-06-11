# DHCP Toolset

Some tools to mess around with DHCP protocol. Useful for Active Directory Attacks or MITM LAN Attacks

- Deploy Rogue DHCP
- Sniff DHCP Discoveries
- MITM with Fake Router/DNS

Keep in mind that you must use other tools to complement MITM attacks with DHCP. For example:
- setting up a custom DNS Server
- configure ip forwarding/traffic inspection when impersonating a gateway
- faulty behaviour due to dhcp's protocol's nature

## Usage

```
usage: dhcptoolset.py [-h] {rogue-dhcp,fake-client} ...

DHCP Toolset

positional arguments:
  {rogue-dhcp,fake-client}
                        Type of script
    rogue-dhcp          Deploy Rogue DHCP
    fake-client         Send fake DHCP requests to the network

options:
  -h, --help            show this help message and exit

```

## Rogue DHCP

```
usage: dhcptoolset.py rogue-dhcp [-h] -i IFACE [-s SERVER] [-r ROUTER] [-o OFFER]

options:
  -h, --help            show this help message and exit
  -i IFACE, --iface IFACE
                        Network interface to listen
  -s SERVER, --server SERVER
                        DHCP Server
  -r ROUTER, --router ROUTER
                        Default Gateway IP
  -o OFFER, --offer OFFER
                        IP to offer to Clients. Defaults to client ip
```


