"""
MCP WhatsApp Server setup script.

@author Bruno Santos
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as f:
    requirements = f.read().splitlines()

setup(
    name="whatsapp-mcp-server",
    version="1.0.0",
    author="Bruno Santos",
    author_email="contact@brunosantos.app",
    description="MCP WhatsApp Server for Claude Desktop integration",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/brunosantos/mcp-whatsapp",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.9",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "whatsapp-mcp=src.server:main",
        ],
    },
)
