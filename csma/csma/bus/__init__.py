"""Ecosystem Bus — typed inter-agent messaging.

The two hand-built pieces that do not exist in any off-the-shelf library:
- schema.py: typed message schema (BusMessage + payload discriminated union)
- translator.py: raw library output ↔ typed payload ↔ natural-language context
"""
