#!/usr/bin/env python3
# SPDX-FileCopyrightText: © 2023 Tenstorrent Inc.
# SPDX-License-Identifier: Apache-2.0

"""
TT-Top executable entry point

This file serves as the main entry point for the tt-top command,
providing a direct path to the live hardware monitoring interface.
"""

from tt_top import main

if __name__ == "__main__":
    main()