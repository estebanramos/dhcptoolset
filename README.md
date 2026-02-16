# DHCP Toolset

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Security](https://img.shields.io/badge/security-tool-red.svg)](https://github.com/estebanramos/dhcptoolset)

A Python toolkit for DHCP protocol manipulation and security testing. Useful for authorized penetration testing, network security assessments, and educational purposes.

## ⚠️ Disclaimer

**This tool is intended for authorized security testing and educational purposes only.** Unauthorized use of this tool on networks you do not own or have explicit permission to test is illegal and may result in criminal charges. The authors and contributors are not responsible for any misuse of this software.

## Features

- 🎯 **Deploy Rogue DHCP Server** - Set up a rogue DHCP server to intercept client requests
- 📡 **Sniff DHCP Discoveries** - Monitor and analyze DHCP traffic on the network
- 🔀 **MITM with Fake Router/DNS** - Configure fake gateway and DNS settings for network interception
- 📊 **Rich Packet Analysis** - Beautiful terminal output with detailed packet information

## Requirements

- Python 3.8 or higher
- Linux, macOS, or Windows (with appropriate network permissions)
- Root/Administrator privileges (required for binding to port 67)

## Installation

### From Source

```bash
# Clone the repository
git clone https://github.com/estebanramos/dhcptoolset.git
cd dhcptoolset

# Install dependencies
pip3 install -r requirements.txt

# Optional: Install as a package
pip3 install -e .
```

### Using pip (when published)

```bash
pip3 install dhcptoolset
```

## Usage

> **⚠️ Root/Administrator Privileges Required**
> 
> DHCP servers must bind to port 67, which is a privileged port (ports below 1024). On Unix-like systems (Linux, macOS), this requires root privileges. The tool will check for this and provide helpful error messages if run without sufficient privileges.

### Rogue DHCP Server

Deploy a rogue DHCP server to respond to client DHCP discovery requests:

```bash
# Basic usage (uses default gateway and random IP)
sudo python3 dhcptoolset.py rogue-dhcp -i eth0

# Specify custom server IP, gateway, and offered IP
sudo python3 dhcptoolset.py rogue-dhcp -i eth0 -s 192.168.1.1 -r 192.168.1.1 -o 192.168.1.100

# Using the installed command
sudo dhcptoolset rogue-dhcp -i eth0
```

**Why sudo?** Port 67 is a privileged port that requires root/administrator access. This is a security feature of the operating system to prevent unauthorized services from binding to system ports.

**Options:**
- `-i, --iface`: Network interface to listen on (required)
- `-s, --server`: DHCP Server IP address (optional, defaults to gateway)
- `-r, --router`: Default Gateway IP address (optional, defaults to gateway)
- `-o, --offer`: IP address to offer to clients (optional, random IP if not specified)

### Fake Client

Send fake DHCP requests to the network (coming soon):

```bash
sudo python3 dhcptoolset.py fake-client -i eth0
```

## Examples

### Example 1: Basic Rogue DHCP Server

```bash
# List available interfaces first
ip link show  # or: ifconfig

# Start rogue DHCP server on eth0
sudo python3 dhcptoolset.py rogue-dhcp -i eth0
```

### Example 2: Custom Configuration

```bash
# Deploy with specific settings
sudo python3 dhcptoolset.py rogue-dhcp \
    -i wlan0 \
    -s 192.168.0.1 \
    -r 192.168.0.1 \
    -o 192.168.0.50
```

## How It Works

1. **DHCP Discovery**: The server listens for DHCP DISCOVER packets from clients
2. **DHCP Offer**: When a discovery is received, the server sends a DHCP OFFER with configured IP settings
3. **DHCP Request**: The client responds with a DHCP REQUEST
4. **DHCP ACK**: The server sends a DHCP ACK to complete the lease

## Important Notes

- **Root Privileges Required**: Port 67 is a privileged port (below 1024) and requires root/administrator privileges on Unix-like systems. This is a security feature of the operating system, not a limitation of this tool.
- **Network Interface**: Must specify a valid network interface on your system
- **Complementary Tools**: For full MITM attacks, you'll need:
  - A custom DNS server (e.g., dnsmasq)
  - IP forwarding enabled
  - Traffic inspection tools (e.g., Wireshark, tcpdump)

## Troubleshooting

### Port Already in Use

If you see "Address already in use", another DHCP server may be running:

```bash
# Linux: Check what's using port 67
sudo netstat -tulpn | grep :67
sudo lsof -i :67

# Stop the service (example for systemd)
sudo systemctl stop isc-dhcp-server
```

### Permission Denied

Ensure you're running with appropriate privileges:

```bash
# Linux/macOS
sudo python3 dhcptoolset.py rogue-dhcp -i eth0

# Windows (run as Administrator)
python dhcptoolset.py rogue-dhcp -i "Ethernet"
```

### Invalid Interface

List available interfaces:

```bash
# Linux
ip link show
ifconfig -a

# macOS
ifconfig -a
networksetup -listallhardwareports

# Windows
ipconfig /all
```

## Roadmap

- [ ] DHCPv6 Support
- [ ] Multi-threading for handling multiple clients
- [ ] Fake client implementation
- [ ] DHCP lease management
- [ ] DNS server integration
- [ ] Web interface for monitoring
- [ ] Packet capture and replay

## Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## References

- [DHCP Protocol (Wikipedia)](https://en.wikipedia.org/wiki/Dynamic_Host_Configuration_Protocol)
- [Microsoft DHCP Basics](https://learn.microsoft.com/en-us/windows-server/troubleshoot/dynamic-host-configuration-protocol-basics)
- [RFC 2131 - DHCP](https://tools.ietf.org/html/rfc2131)

## Security

If you discover a security vulnerability, please send an email to the maintainers. Do not open a public issue.

## Support

- 📖 [Documentation](https://github.com/estebanramos/dhcptoolset#readme)
- 🐛 [Report a Bug](https://github.com/estebanramos/dhcptoolset/issues)
- 💡 [Request a Feature](https://github.com/estebanramos/dhcptoolset/issues)
- 💬 [Discussions](https://github.com/estebanramos/dhcptoolset/discussions)

## Acknowledgments

- Built with [Rich](https://github.com/Textualize/rich) for beautiful terminal output
- Uses [Colorama](https://github.com/tartley/colorama) for cross-platform colored output
- Network interface detection via [netifaces](https://github.com/al45tair/netifaces)

---

**Remember**: Only use this tool on networks you own or have explicit written permission to test. Unauthorized access to computer networks is illegal.