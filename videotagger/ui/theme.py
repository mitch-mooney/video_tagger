"""VideoTagger — Broadcast Studio theme tokens.

Single source of truth for the palette and font stacks. Both the global stylesheet
(``style.py``) and the widgets that style themselves inline (header, transport,
shortcut bar, timeline) import from here, so a colour or font changes in one place.

Fonts are Windows-native (no bundling): ``Bahnschrift`` is the DIN-style condensed
display face shipped with Windows 10/11; ``Cascadia Mono`` is used for timecodes.
"""
from __future__ import annotations

# ── Surfaces (three elevations + the deepest, for the video surround) ──────
INK        = "#0a0e14"   # app base
INK_DEEP   = "#06090e"   # video surround / deepest wells
SURFACE    = "#111824"   # panels
SURFACE_2  = "#161f2d"   # elevated panels / inputs hover
LINE       = "#232d3d"   # hairlines
LINE_SOFT  = "#19212f"   # inner separators

# ── Text ──────────────────────────────────────────────────────────────────
TEXT       = "#e8eef6"   # ≈14:1 on INK (AAA)
MUTED      = "#7e90a8"
FAINT      = "#4a5a70"

# ── Accent (brand / interaction; team-swappable) ──────────────────────────
ACCENT       = "#15e6c4"
ACCENT_DIM   = "#0c8d7c"
ACCENT_LIGHT = "#5cf3da"

# ── Signal (reserved exclusively for the armed "marking" state) ───────────
SIGNAL     = "#ffb020"   # amber
SIGNAL_DIM = "#5a4413"

# ── Default category colours (used when a category has none / for fallback) ─
CAT_FALLBACK = "#557799"

# ── Fonts ──────────────────────────────────────────────────────────────────
FONT_DISPLAY = '"Bahnschrift SemiBold", "Bahnschrift", "Segoe UI Semibold", "Segoe UI", sans-serif'
FONT_BODY    = '"Segoe UI Variable Text", "Segoe UI", "SF Pro Text", system-ui, sans-serif'
FONT_MONO    = '"Cascadia Mono", "Cascadia Code", "Consolas", monospace'


def shade(hex_color: str, factor: float) -> str:
    """Scale an ``#rrggbb`` colour's channels by ``factor`` (clamped to 0–255)."""
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    r, g, b = (min(255, int(c * factor)) for c in (r, g, b))
    return f"#{r:02x}{g:02x}{b:02x}"


DEFAULT_ACCENT = ACCENT  # the brand teal, before any team-colour override


def set_accent(hex_color: str) -> None:
    """Rebind the runtime accent (and its derived dim/light shades).

    The team-colour feature calls this so the *whole* UI follows one accent.
    Inline-styled widgets read ``theme.ACCENT`` when they build or repaint, so
    call this BEFORE building the UI (at startup) or restyle those widgets after.
    """
    global ACCENT, ACCENT_DIM, ACCENT_LIGHT
    ACCENT = hex_color
    ACCENT_DIM = shade(hex_color, 0.62)
    ACCENT_LIGHT = shade(hex_color, 1.2)
