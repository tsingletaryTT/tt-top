#!/usr/bin/env python3
"""
Setup.py for TT-Top - Standalone Tenstorrent Hardware Monitor.
Forked from TT-SMI to create a dedicated real-time monitoring tool.
"""
from setuptools import setup, find_packages

import tomli

if __name__ == "__main__":
    with open("pyproject.toml", "rb") as f:
        toml_data = tomli.load(f)

    setup(
        # TT-Top specific configuration
        name="tt-top",
        version=toml_data['project']['version'],
        packages=find_packages(),
        python_requires=">=3.10",
        entry_points={
            'console_scripts': [
                'tt-top = tt_top:main',
            ]
        },
    )