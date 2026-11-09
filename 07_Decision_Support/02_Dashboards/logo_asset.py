"""
================================================================================
CHER-CDSS: Official N-HYPPADEC Logo & Seal Asset Helper
================================================================================
Module: logo_asset.py
Directory: 07_Decision_Support/02_Dashboards/
Author: N-HYPPADEC CDSS Engineering Team
Purpose:
  Provides centralized access to the official N-HYPPADEC seal & heraldry,
  including filesystem paths, FileResponse streaming, and offline-compatible
  Base64 Data URIs for executive print dossiers and Web GIS UI components.
================================================================================
"""

import os
import base64
from typing import Optional

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
LOGO_JPG_PATH = os.path.join(STATIC_DIR, "nhyppadec_logo.jpg")
LOGO_PNG_PATH = os.path.join(STATIC_DIR, "nhyppadec_logo.png")

_CACHED_DATA_URI: Optional[str] = None

def get_logo_filepath() -> str:
    """Returns the absolute path to the official logo file."""
    if os.path.exists(LOGO_JPG_PATH):
        return LOGO_JPG_PATH
    return LOGO_PNG_PATH

def get_logo_bytes() -> bytes:
    """Reads raw bytes of the official logo."""
    path = get_logo_filepath()
    with open(path, "rb") as f:
        return f.read()

def get_logo_data_uri() -> str:
    """
    Returns an offline-compatible Base64 Data URI string
    (e.g. data:image/jpeg;base64,...) for embedding in HTML, executive PDFs,
    and SVG canvases without web server URL dependency.
    """
    global _CACHED_DATA_URI
    if _CACHED_DATA_URI:
        return _CACHED_DATA_URI

    path = get_logo_filepath()
    if os.path.exists(path):
        with open(path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("utf-8")
            _CACHED_DATA_URI = f"data:image/jpeg;base64,{b64}"
            return _CACHED_DATA_URI
    return ""

