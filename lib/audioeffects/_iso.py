"""ISO centre frequencies, kept as a shared private constant.

The old family GraphicEQ walked these ten centres. The rebuilt GraphicEQ
uses the M-108 octave doublings instead (`DEFAULT_CENTRES` on that class).
Tests that still pin a +6 dB bell on the ISO series import this tuple;
nothing else in the package does, and `_SingleFilter` died with the old
LowPass / HighPass / BandPass / Notch classes that were the only users.
"""

ISO_BANDS = (31.5, 63.0, 125.0, 250.0, 500.0,
             1000.0, 2000.0, 4000.0, 8000.0, 16000.0)
