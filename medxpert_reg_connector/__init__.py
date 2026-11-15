# -*- coding: utf-8 -*-
"""MedXpert reg-connector: read-only local MCP server for global medical-device regulation."""

try:  # single source of truth: the installed distribution version
    from importlib.metadata import version as _dist_version

    __version__ = _dist_version("medxpert-reg-connector")
except Exception:  # source tree without an installed distribution
    __version__ = "0.0.0"
__all__ = ["__version__"]
