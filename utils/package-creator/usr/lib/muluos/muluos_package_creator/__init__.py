"""MuluOS package creator.

Builds MuluOS .exe application bundles (opaque directories with Info.json,
the executable, bundled dependencies, and multi-size icons) and optional
self-contained installer bundles. The build/icon/template logic lives in
builder.py; widget.py is the PyQt6 UI; app.py is the standalone window.
"""
