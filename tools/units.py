"""
units.py - metric <-> US customary unit conversion for Live Stage Toolkit
GUIs.

The calculation engine (stage_rig_calculator.py) works entirely in metric
(metres, lux, candela/m^2) - that does not change, and should not: mixing
unit systems inside the physics is a far easier place to introduce a silent
error than converting for display at the edges. This module is purely a
GUI-facing conversion layer, the same principle already used for language
(i18n.py) and for the screen-surface choice (an internal code, never parsed
display text): convert at the boundary, keep the core in one system.

No dependencies beyond the Python standard library.

Part of the Live Stage Toolkit. MIT licence.
"""

from __future__ import annotations

DEFAULT_UNIT_SYSTEM = "metric"
UNIT_SYSTEMS = ("metric", "imperial")

# --- Conversion factors ---
# 1 international foot = 0.3048 m exactly, by definition (1959 agreement).
METRES_PER_FOOT = 0.3048

# 1 footcandle = 1 lumen per square foot. 1 sq ft = 0.09290304 sq m exactly,
# so 1 fc = 1 / 0.09290304 lux.
LUX_PER_FOOTCANDLE = 1.0 / 0.09290304

# 1 foot-Lambert = (1/pi) candela per square foot.
# nits (cd/m^2) per foot-Lambert = (1/pi) / 0.09290304
import math as _math
NITS_PER_FOOTLAMBERT = (1.0 / _math.pi) / 0.09290304


def m_to_ft(value_m: float) -> float:
    return value_m / METRES_PER_FOOT


def ft_to_m(value_ft: float) -> float:
    return value_ft * METRES_PER_FOOT


def lux_to_fc(value_lux: float) -> float:
    return value_lux / LUX_PER_FOOTCANDLE


def fc_to_lux(value_fc: float) -> float:
    return value_fc * LUX_PER_FOOTCANDLE


def nits_to_fl(value_nits: float) -> float:
    """Nits (candela/m^2) to foot-Lamberts. Not currently displayed anywhere
    in the GUI (screen luminance is only shown as a pass/fail verdict, not a
    raw number) - included now because the Producer is planning further
    development of this script and asked for exactly this kind of
    forward-looking infrastructure."""
    return value_nits / NITS_PER_FOOTLAMBERT


def fl_to_nits(value_fl: float) -> float:
    return value_fl * NITS_PER_FOOTLAMBERT


def selftest() -> int:
    # Known reference points, not just round-trips - a round-trip test alone
    # would happily pass even with a consistently-inverted or doubled factor.
    assert abs(m_to_ft(1.0) - 3.28084) < 1e-4, m_to_ft(1.0)
    assert abs(ft_to_m(1.0) - 0.3048) < 1e-9, ft_to_m(1.0)
    assert abs(m_to_ft(0.3048) - 1.0) < 1e-9

    # SMPTE cross-check: the engine's TARGET_SCREEN_NITS = 48.0 should land
    # close to the US cinema industry-standard 14 foot-Lamberts - this is
    # the exact cross-check mentioned to the Producer when this module was
    # proposed.
    fl = nits_to_fl(48.0)
    assert abs(fl - 14.0) < 0.1, fl

    # 500 lux (a common well-lit-office reference point) is roughly 46.45 fc.
    fc = lux_to_fc(500.0)
    assert abs(fc - 46.45) < 0.1, fc

    # Round-trip sanity in both directions, on top of the fixed points above -
    # catches a swapped multiply/divide that a fixed-point check alone might
    # not, across a spread of magnitudes relevant to this toolkit (sub-metre
    # camera offsets up to multi-metre stage dimensions).
    for v in (0.001, 1.0, 7.0, 1234.5):
        assert abs(ft_to_m(m_to_ft(v)) - v) < 1e-9, v
        assert abs(fc_to_lux(lux_to_fc(v)) - v) < 1e-9, v
        assert abs(fl_to_nits(nits_to_fl(v)) - v) < 1e-9, v

    print("SELFTEST OK")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(selftest())
