# Contributing to DHCP Toolset

Thank you for your interest in contributing to DHCP Toolset! This document provides guidelines and instructions for contributing.

## Code of Conduct

- Be respectful and inclusive
- Welcome newcomers and help them learn
- Focus on constructive feedback
- Report any issues or concerns

## How to Contribute

### Reporting Bugs

1. Check if the bug has already been reported in the Issues section
2. If not, create a new issue with:
   - A clear, descriptive title
   - Steps to reproduce the bug
   - Expected vs actual behavior
   - Your environment (OS, Python version, etc.)
   - Any relevant error messages or logs

### Suggesting Features

1. Check if the feature has already been suggested
2. Create a new issue with:
   - A clear description of the feature
   - Use cases and examples
   - Potential implementation approach (if you have ideas)

### Submitting Code Changes

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/your-feature-name`
3. **Make your changes**:
   - Follow the existing code style
   - Add comments and docstrings where appropriate
   - Test your changes thoroughly
4. **Commit your changes**: `git commit -m "Add feature: description"`
   - Use clear, descriptive commit messages
5. **Push to your fork**: `git push origin feature/your-feature-name`
6. **Create a Pull Request**:
   - Provide a clear description of your changes
   - Reference any related issues
   - Include screenshots or examples if applicable

## Development Setup

1. Clone your fork: `git clone https://github.com/estebanramos/dhcptoolset.git`
2. Create a virtual environment: `python3 -m venv venv`
3. Activate it: `source venv/bin/activate` (Linux/Mac) or `venv\Scripts\activate` (Windows)
4. Install dependencies: `pip install -r requirements.txt`
5. Install in development mode: `pip install -e .`

## Code Style

- Follow PEP 8 style guidelines
- Use meaningful variable and function names
- Add docstrings to functions and classes
- Keep functions focused and modular
- Add comments for complex logic

## Testing

- Test your changes before submitting
- Test on different operating systems if possible
- Test edge cases and error conditions

## Security Considerations

- This tool is for authorized security testing only
- Do not add features that could be easily misused
- Report security vulnerabilities privately

## Questions?

Feel free to open an issue for any questions or concerns about contributing.

Thank you for contributing to DHCP Toolset!
