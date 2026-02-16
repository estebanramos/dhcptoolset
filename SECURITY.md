# Security Policy

## Supported Versions

We release patches for security vulnerabilities. Which versions are eligible for receiving such patches depends on the CVSS v3.0 Rating:

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |

## Reporting a Vulnerability

If you discover a security vulnerability in this project, please report it responsibly:

1. **Do NOT** open a public GitHub issue
2. Email the maintainers directly with details about the vulnerability
3. Include:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if you have one)

We will acknowledge receipt of your report within 48 hours and provide an update on the status of the vulnerability within 7 days.

## Security Considerations

This tool is designed for authorized security testing and educational purposes. However, users should be aware of:

- **Network Impact**: Running a rogue DHCP server can disrupt network services
- **Legal Implications**: Unauthorized use may violate computer fraud and abuse laws
- **Privilege Escalation**: Requires root/administrator privileges to bind to port 67
- **Network Exposure**: May expose your system to network-based attacks

## Best Practices

- Only use this tool on networks you own or have explicit written permission to test
- Use in isolated lab environments when learning
- Keep the tool updated to the latest version
- Review code changes before deploying
- Use proper network isolation when testing

## Responsible Disclosure

We follow responsible disclosure practices:
- Vulnerabilities will be patched as quickly as possible
- Security updates will be released with appropriate version bumps
- Credit will be given to security researchers who responsibly report issues
- Public disclosure will occur after a patch is available (typically 30-90 days)

## Contact

For security-related issues, please contact the maintainers directly rather than opening a public issue.
