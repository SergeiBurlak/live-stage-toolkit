#!/usr/bin/env python3
"""
theme.py - named colour tokens for the Live Stage Toolkit GUI's chrome:
window background, ttk widgets (frames, labelframes, buttons, tabs,
entries, comboboxes), the classic Tk menu bar, and the two log/report
Text widgets.

Same "no dependencies beyond the standard library" rule as the rest of
this toolkit - nothing here beyond stdlib. The tkinter/ttk glue that
actually applies these tokens lives in stage_rig_gui.py (StageRigApp's
own _apply_theme()), which already owns the one Tk root - the same split
stage_rig_calculator.py/stage_rig_gui.py already use for engine vs GUI.

Only three of the Theme menu's four choices have a token dict here.
"Standard" is the fourth choice: this OS/Tk build's own native look, left
completely alone rather than replaced by a dict from this file -
stage_rig_gui.py restores the colours it captured before any theme was
first applied. That is why THEMES below has no "standard" key.

Part of the Live Stage Toolkit. MIT licence.
"""
from __future__ import annotations

# One accent colour, shared by "dark" and "light" (the Notebook's selected
# tab, focused field borders) instead of a different accent per theme.
# Chosen by measurement: the colour that clears the WCAG AA bar (4.5:1)
# for white text drawn on it, and also clears the lower WCAG "UI
# component" bar (3:1) against both themes' own window background below -
# see selftest(). "dark_green" below deliberately does NOT reuse this -
# a cool blue accent read as an afterthought on a warm forest-green
# ground (checked by eye, not just computed) - it gets its own gold
# accent instead, checked against the exact same selftest() bars.
ACCENT_COLOR = "#2563EB"

THEMES: dict[str, dict[str, str]] = {
    "dark": {
        "accent": ACCENT_COLOR,
        # Not pure black (#000000) - avoids the "halo" look light text
        # gets around it on a fully black background.
        "window": "#121212",
        "surface": "#1E1E1E",        # Entry/Combobox/Text field backgrounds
        "text": "#E8E8E8",
        "text_secondary": "#A0A0A0",
        "border": "#3A3A3A",
        "select_bg": ACCENT_COLOR,
        "select_fg": "#FFFFFF",
        "disabled_text": "#6E6E6E",
        # The probe log's PASS/WARN/FAIL tag colours (ok/warn/bad) predate
        # this theme system and were tuned for a plain white log
        # background (light theme keeps those exact values below,
        # unchanged). Measured against THIS theme's dark surface, they
        # fall short of 4.5:1 (2.97-3.42) - so dark gets its own brighter
        # variants instead of silently reusing colours picked for a
        # different background.
        "status_ok": "#3FB950",
        "status_warn": "#D29922",
        "status_bad": "#FF6B6B",
    },
    "light": {
        "accent": ACCENT_COLOR,
        "window": "#F4F4F5",
        "surface": "#FFFFFF",
        "text": "#1C1C1E",
        "text_secondary": "#5B5B5E",
        "border": "#D3D3D6",
        "select_bg": ACCENT_COLOR,
        "select_fg": "#FFFFFF",
        "disabled_text": "#A0A0A3",
        # Unchanged from the colours this GUI already used for the probe
        # log before the Theme menu existed - already comfortably above
        # 4.5:1 against a white surface (measured: 4.87-5.62).
        "status_ok": "#1a7f37",
        "status_warn": "#9a6700",
        "status_bad": "#c62828",
    },
    "dark_green": {
        # Deep forest green, not a hue-shifted copy of "dark" - a gold
        # accent (not ACCENT_COLOR above) pairs with it, the classic
        # forest/brass combination, and reads as its own identity rather
        # than "dark theme with a green cast". Lightened +feedback
        # round 1 (Сергей, 2026-10-21/22): "зелёный слишком тёмный, почти
        # не отличается от чёрного... золотой ярче" - window/surface/
        # border raised ~20% in HSL lightness (same hue/saturation, just
        # lighter), accent pushed to a more saturated, more vivid gold
        # (S 0.68->0.90, L 0.47->0.58) rather than the original antique-
        # gold. status_bad/disabled_text re-tuned afterward since the
        # lighter surface ate into their own contrast margin against it -
        # not eyeballed, re-measured with this file's own contrast_ratio()
        # the same way the original values were.
        "accent": "#F4C634",
        "window": "#202F26",
        "surface": "#2E4438",         # Entry/Combobox/Text field backgrounds
        "text": "#E8ECE6",
        "text_secondary": "#9FB3A4",
        "border": "#466250",
        "select_bg": "#F4C634",
        # Gold is light enough that white selection text would fail
        # WCAG AA against it (unlike select_fg in the other two themes,
        # which pairs a light select_fg with a DARK select_bg) - this
        # theme's own select_fg is dark instead, see selftest().
        "select_fg": "#13190E",
        "disabled_text": "#798C7E",
        # Conventional ok/warn/bad hues (green/amber/red), independent of
        # this theme's own forest/gold identity - tuned bright enough for
        # this specific dark surface, same reasoning as "dark" above.
        "status_ok": "#5FD38A",
        "status_warn": "#E3B341",
        "status_bad": "#FF9891",
    },
}


def _srgb_to_linear(channel_0_1: float) -> float:
    c = channel_0_1
    return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4


def relative_luminance(hex_color: str) -> float:
    """WCAG 2.x relative luminance (0 = black, 1 = white) of a "#RRGGBB"
    colour - the shared building block contrast_ratio() below is defined
    in terms of."""
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4))
    r, g, b = _srgb_to_linear(r), _srgb_to_linear(g), _srgb_to_linear(b)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast_ratio(hex_a: str, hex_b: str) -> float:
    """WCAG 2.x contrast ratio between two colours (>=1.0 always; 21.0 is
    pure black against pure white). 4.5:1 is the WCAG AA bar for normal
    text; 3:1 is the lower bar for large text and for essential
    UI-component boundaries (WCAG 1.4.11)."""
    l1, l2 = relative_luminance(hex_a), relative_luminance(hex_b)
    lighter, darker = max(l1, l2), min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


def selftest() -> int:
    names = list(THEMES)
    reference = set(THEMES[names[0]])
    for name in names[1:]:
        assert set(THEMES[name]) == reference, \
            f"{name}: must define the same set of tokens as {names[0]!r}"

    for name, tokens in THEMES.items():
        assert contrast_ratio(tokens["text"], tokens["window"]) >= 4.5, \
            f"{name}: text/window below WCAG AA"
        assert contrast_ratio(tokens["text"], tokens["surface"]) >= 4.5, \
            f"{name}: text/surface (Entry/Text fields) below WCAG AA"
        assert contrast_ratio(tokens["text_secondary"], tokens["window"]) >= 4.5, \
            f"{name}: text_secondary/window below WCAG AA"
        assert contrast_ratio(tokens["select_fg"], tokens["select_bg"]) >= 4.5, \
            f"{name}: select_fg/select_bg (selected tab, selected field text) below WCAG AA"
        assert contrast_ratio(tokens["accent"], tokens["window"]) >= 3.0, \
            f"{name}: accent/window below the WCAG UI-component bar"
        assert contrast_ratio(tokens["border"], tokens["window"]) >= 1.3, \
            f"{name}: border is barely distinguishable from window"
        for status_key in ("status_ok", "status_warn", "status_bad"):
            assert contrast_ratio(tokens[status_key], tokens["surface"]) >= 4.5, \
                f"{name}: {status_key}/surface (probe log text) below WCAG AA"

    print("SELFTEST OK")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(selftest())
