"""Setup configuration for DHCP Toolset."""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

# Read requirements
requirements_file = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_file.exists():
    requirements = [
        line.strip()
        for line in requirements_file.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    ]

setup(
    name="dhcptoolset",
    version="1.0.0",
    description="A Python toolkit for DHCP protocol manipulation and security testing",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="DHCP Toolset Contributors",
    author_email="",
    url="https://github.com/estebanramos/dhcptoolset",
    license="MIT",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Information Technology",
        "Topic :: Security",
        "Topic :: System :: Networking",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "dhcptoolset=dhcptoolset:main",
        ],
    },
    keywords="dhcp network security pentesting",
    project_urls={
        "Bug Reports": "https://github.com/estebanramos/dhcptoolset/issues",
        "Source": "https://github.com/estebanramos/dhcptoolset",
        "Documentation": "https://github.com/estebanramos/dhcptoolset#readme",
    },
)
