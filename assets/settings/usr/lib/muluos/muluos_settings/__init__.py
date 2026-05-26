"""MuluOS Settings — extensible PyQt6 settings shell.

The shell hosts a sidebar of Panels. Each Panel is a subclass of
muluos_settings.panel.Panel. Built-in panels live under .panels; the
list is hard-coded in main.discover_panels() for now and can be
extended by dropping new Panel subclasses into .panels and adding
them to the discovery list.
"""
