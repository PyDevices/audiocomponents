"""`RingMod` rebuild. The class lives in `rebuilt/ringmod.py` until adopted;
this module re-exports it so tests and a later come-home move share one
implementation. The package still serves `modulation.RingMod`.
"""

from .rebuilt.ringmod import (  # noqa: F401
    RingMod, VENDOR, FREQ, DEPTH, MIX, SHAPE, BAL, PBAL, SQUELCH, THRESH,
    RELEASE, CLOW, PHASE, CHAR, Q15, TABLE_FRAMES, TARGET_FRAMES,
    MAX_CARRIER_FRAMES, MAKEUP_DB, carrier_gain, bandlimited_odd,
)
