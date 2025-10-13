# SPDX-FileCopyrightText: © 2023 Tenstorrent Inc.
# SPDX-License-Identifier: Apache-2.0

"""
TT-Top - Real-time hardware monitoring for Tenstorrent silicon
A standalone fork of TT-SMI focused on live hardware visualization
"""

from .tt_top_app import main

__version__ = "1.0.0"
__all__ = ["main"]