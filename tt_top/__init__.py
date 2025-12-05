# SPDX-FileCopyrightText: © 2023 Tenstorrent Inc.
# SPDX-License-Identifier: Apache-2.0

"""
TT-Top - Real-time hardware monitoring for Tenstorrent silicon
A standalone fork of TT-SMI focused on live hardware visualization
"""

__version__ = "1.0.0"


def main():
    """Lazy import of main to avoid loading heavy dependencies on package import"""
    from .tt_top_app import main as _main
    return _main()


__all__ = ["main"]