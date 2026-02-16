# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2024-XX-XX

### Added
- Initial release of DHCP Toolset
- Rogue DHCP server functionality
- DHCP packet parsing and construction
- Rich terminal output with packet analysis
- Network interface detection and validation
- IP address validation utilities
- Command-line interface with argparse
- Support for custom DHCP server, gateway, and offered IP configuration
- Automatic IP generation from network interface
- Comprehensive documentation (README, CONTRIBUTING, SECURITY)
- MIT License
- Professional project structure with setup.py and pyproject.toml

### Security
- Added security disclaimer and warnings
- Created SECURITY.md for responsible disclosure
- Added proper error handling to prevent information leakage

### Documentation
- Comprehensive README with examples and troubleshooting
- CONTRIBUTING.md for contributor guidelines
- SECURITY.md for security policy
- GitHub issue templates for bugs and features
- Code docstrings for main functions and classes

### Fixed
- Fixed OSError string comparison bug in dhcp_server.py
- Fixed DHCPMessage class reference issue in model.py
- Fixed hardcoded IP addresses in DHCPOFFER and DHCPPACK classes
- Improved error handling with proper exception catching
- Fixed DHCPPACK missing DHCPOptions6 in packet construction

### Changed
- Improved code structure and organization
- Enhanced error messages with better formatting
- Better exception handling throughout the codebase
- Improved .gitignore to exclude logs and build artifacts

### Technical
- Added proper package structure with __init__.py
- Created setup.py for package installation
- Added pyproject.toml for modern Python packaging
- Improved code quality with docstrings
- Better separation of concerns

## [Unreleased]

### Planned
- DHCPv6 Support
- Multi-threading for handling multiple clients
- Fake client implementation
- DHCP lease management
- DNS server integration
- Web interface for monitoring
- Packet capture and replay functionality

---

[1.0.0]: https://github.com/estebanramos/dhcptoolset/releases/tag/v1.0.0
