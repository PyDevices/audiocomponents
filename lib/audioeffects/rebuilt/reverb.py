"""`Reverb` - Dattorro's plate network, cut four ways: a plate, a room, a
chamber and a hall.

Your dry signal passes untouched and a reverb tail rises behind it.
Character picks the machine: `plate` is dense from the first milliseconds,
the way the EMT 140's steel sheet is, while `room`, `chamber` and `hall`
start sparse and build. Decay (0.3 to 10 s) sets how long the tail rings,
Size (0.5 to 1.5) stretches every line of the network, and Predelay (0 to
200 ms) holds the tail back from the dry. Diffusion (0 to 0.9) smears the
early echoes, Damping (500 Hz to 16 kHz) darkens the tail as it rings, and
Bandwidth (500 Hz to 20 kHz) darkens what goes in. Low Cut (20 to 500 Hz)
keeps the bass out of the tank while the dry keeps it. Mod Depth (0 to 2 ms)
and Mod Rate (0.1 to 5 Hz) wobble two lines inside the tank, Width (0 to 1)
sets the stereo spread, and Tone (-12 to +12 dB) tilts the tail. Mix (0 to
2) is `audiodelays.Echo`'s: the dry at unity until 1, the tail alone at 2.
Mix 0 is a byte-exact wire while the tank keeps ringing behind it. Latency
is zero: nothing looks ahead, and Predelay delays only the tail.

On the plate, Decay also moves the tail's loss corner, the way the EMT
140's damping panel does: open at Decay 8 s and above, at the Damping
setting at 1 s and below.

A Character or Size move re-cuts the tank: the tail drops to nothing at the
move, and the dry carries on without losing a frame. `reset()` empties the
tank the same way, keeps the dry, and restores patch 0.

**Decay.** At each character's reference patch (Steel Plate, Live Room,
Dark Chamber, Concert Hall) at Size 1.0, the tail falls 60 dB at 500 Hz
within 12 % of Decay at 2, 3, 4, 6, 8 and 10 s, and on the hall from 4 s.
Shorter Decays, other Sizes and the other patches are not claimed: Damped
Plate, Small Room and Live Room ring longer than their Decay reads. With
Damping at 1 kHz and Size 0.5, the room, chamber and hall at Decay 8 and
10 s ring more than 12 % short of it: the class holds the bass to 1.5 x
Decay.

**Modulation.** With Mod Depth at 0, a 1 kHz tone on Steel Plate or Concert
Hall comes out as one line, its sidebands more than 60 dB under it. On those
two patches as shipped, at every grid position from 17 to 64 of Mod Depth
(about 0.27 to 1 ms) and from 45 to 81 of Mod Rate (about 0.4 to 1.2 Hz),
tones at 300 Hz, 1 kHz and 3 kHz spread into sidebands within 20 dB of the
tone. Outside that it is not claimed: on Steel Plate a 3 kHz tone at Mod
Depth position 81 (about 1.28 ms) and Mod Rate position 121 (about 4.16 Hz)
reads more than 20 dB under.

**Input ceiling.** There is no input gain, and the tank's lines clamp at the
rail on every write whatever Mix is: a steady 362 Hz tone at 8 000 LSB RMS
comes back more than 1 dB quieter in the tail than at 4 000. On 2 s of
uniform noise at 4 000 LSB RMS at Mix 1, no shipped patch reaches the rail
at 48, 44.1 or 22.05 kHz; Bright Chamber at 44.1 kHz is not claimed.

**The patches:** Steel Plate (the defaults), Short Plate, Damped Plate,
Bass-Free Plate, Small Room, Live Room, Concert Hall, Dark Chamber, Bright
Chamber, Slow Bloom.

`tail_samples` bounds the frames until the output is exactly zero once
your input stops: 222 868 frames at the defaults at 48 kHz. One int16
allocation holds the lines and 200 ms of predelay: 89 714 B for Steel Plate
at 48 kHz, and 146 914 B for the hall at Size 1.5, the most it takes.

**Limits shared by the family**

A control that jumps makes the output step: move it in small steps from
the host if you need it smooth.

When your source ends, the tail rings out as it would on silence.

Asking for `character="spring"` says it is parked: the tank has no
dispersive chain yet. A value outside a macro's span clamps to the nearer
stop, and NaN takes the option's default. On a board without `audioverb`,
construction raises `ImportError`.
"""

VENDOR = "PyDevices"

import math

from .. import _component

try:
    import audioverb
except ImportError:                     # pragma: no cover - a stock board
    audioverb = None


#: Dattorro's reference rate: his Fig. 1 lengths are frames at 29 761 Hz.
REF_RATE = 29761.0

#: Dattorro Fig. 1's twelve lines, in the Tank's order: four input
#: diffusers, then half A (modulated all-pass, delay, all-pass, delay) and
#: half B the same.
DATTORRO_LINES = (142, 107, 379, 277, 672, 4453, 1800, 3720,
                  908, 4217, 2656, 3163)

#: Dattorro Table 2's fourteen output taps, (channel, line, offset, gain).
DATTORRO_TAPS = (
    (0, 9, 266, 0.6), (0, 9, 2974, 0.6), (0, 10, 1913, -0.6),
    (0, 11, 1996, 0.6), (0, 5, 1990, -0.6), (0, 6, 187, -0.6),
    (0, 7, 1066, -0.6),
    (1, 5, 353, 0.6), (1, 5, 3627, 0.6), (1, 6, 1228, -0.6),
    (1, 7, 2673, 0.6), (1, 9, 2111, -0.6), (1, 10, 335, -0.6),
    (1, 11, 121, -0.6),
)

CHARACTERS = ("plate", "room", "chamber", "hall")
PLATE, ROOM, CHAMBER, HALL = range(4)

#: Each character's ratio over Dattorro's twelve lines (dossier App. A8.8).
#: The plate is his tank with its input diffusers at 0.3 of his, so the
#: density is there by 20 ms (T1); the others stretch the diffusers so the
#: density builds (T8) and re-proportion the tank. No two rows are
#: proportional, so no Size makes two characters' line sets equal (T9).
RATIOS = (
    (0.30, 0.30, 0.30, 0.30, 1.00, 1.00, 1.00, 1.00,
     1.00, 1.00, 1.00, 1.00),
    (4.50, 4.20, 3.40, 3.70, 0.50, 0.36, 0.44, 0.40,
     0.52, 0.38, 0.42, 0.37),
    (4.00, 4.30, 3.00, 3.40, 0.80, 0.62, 0.70, 0.66,
     0.78, 0.64, 0.72, 0.60),
    (2.00, 1.86, 1.60, 1.78, 1.30, 1.12, 1.24, 1.08,
     1.26, 1.16, 1.20, 1.10),
)

#: The Decay law's per-character constant (dossier section 4), each a
#: multiple of 1/64 so every float format holds it exactly.
KAPPA = (1.078125, 1.046875, 1.078125, 1.046875)

#: The Decay law's low-frequency ceiling: the loop's bass never rings longer
#: than LF_CAP x Decay (dossier section 4; the 1.5 is the design's).
LF_CAP = 1.5

#: The node refuses a line under 4 frames (`audiodsp_tank.c:145-146`); the
#: shortest the class cuts anywhere on its span is 12.
MIN_LINE = 4

#: The Tank's predelay allocation, fixed at construction; the Predelay
#: macro's top.
MAX_PREDELAY_MS = 200.0

#: Where each character's zone sits on the 0-127 grid when the constructor
#: or a patch names it: plate 0-31, room 32-63, chamber 64-95, hall 96-127.
CHARACTER_MIDI = (0, 42, 85, 127)

#: The plate's damper law: open at DAMPER_LONG_S, the Damping setting at
#: DAMPER_SHORT_S, geometric in log Decay between (dossier section 4, T3).
DAMPER_LONG_S = 8.0
DAMPER_SHORT_S = 1.0

#: The frequency Decay is stated at.
DECAY_HZ = 500.0

(CHARACTER_I, DECAY_I, SIZE_I, PREDELAY_I, DIFFUSION_I, DAMPING_I,
 BANDWIDTH_I, LOW_CUT_I, MOD_DEPTH_I, MOD_RATE_I, WIDTH_I, TONE_I,
 MIX_I) = range(13)

#: The constructor defaults, in macro order, which NaN falls back to.
DEFAULTS = (0.0, 2.4, 1.0, 0.0, 0.75, 1000.0, 12000.0, 40.0, 0.27, 1.0,
            1.0, 0.0, 0.35)


# -- the cut -----------------------------------------------------------------

def line_set(index, size, sample_rate, ratios=None):
    """The twelve line lengths, in frames, of character `index` at `size`
    and `sample_rate`: round(n x fs / 29 761 x size x r) per line."""
    ratios = RATIOS[index] if ratios is None else ratios
    fs = float(sample_rate)
    size = float(size)
    out = []
    for n, r in zip(DATTORRO_LINES, ratios):
        frames = int(round(n * fs / REF_RATE * size * r))
        out.append(frames if frames > MIN_LINE else MIN_LINE)
    return out


def tap_table(index, size, sample_rate, ratios=None, lines=None):
    """The fourteen taps, flattened as the Tank takes them: each offset
    scaled by its own line's factor and held under that line's length."""
    ratios = RATIOS[index] if ratios is None else ratios
    if lines is None:
        lines = line_set(index, size, sample_rate, ratios)
    fs = float(sample_rate)
    size = float(size)
    out = []
    for channel, line, offset, gain in DATTORRO_TAPS:
        at = int(round(offset * fs / REF_RATE * size * ratios[line]))
        if at > lines[line] - 1:
            at = lines[line] - 1
        out.extend((channel, line, at, gain))
    return out


def half_periods(lines):
    """Frames around each half of the figure-eight: lines 4-7 and 8-11."""
    return (lines[4] + lines[5] + lines[6] + lines[7],
            lines[8] + lines[9] + lines[10] + lines[11])


# -- the laws ----------------------------------------------------------------

def one_pole_mag(corner_hz, frequency, sample_rate):
    """|H| at `frequency` of the node's loop one-pole, whose coefficient is
    1 - exp(-2 pi corner / fs)."""
    if corner_hz <= 0.0:
        return 1.0
    a = 1.0 - math.exp(-2.0 * math.pi * corner_hz / sample_rate)
    w = 2.0 * math.pi * frequency / sample_rate
    b = 1.0 - a
    re = 1.0 - b * math.cos(w)
    im = b * math.sin(w)
    return a / math.sqrt(re * re + im * im)


def damper_hz(decay_s, damping_hz, sample_rate):
    """The plate's loop corner at a Decay: 0.98 x Nyquist at 8 s and above,
    `damping_hz` at 1 s and below, geometric in log Decay between."""
    top = 0.98 * sample_rate * 0.5
    t = decay_s
    if t < DAMPER_SHORT_S:
        t = DAMPER_SHORT_S
    if t > DAMPER_LONG_S:
        t = DAMPER_LONG_S
    x = math.log(DAMPER_LONG_S / t) / math.log(DAMPER_LONG_S / DAMPER_SHORT_S)
    return top * (damping_hz / top) ** x


def decay_law(kappa, lines, sample_rate, decay_s, loop_hz):
    """The Tank's `decay` for a T60 of `decay_s` at 500 Hz.

    One pass through a half multiplies by `decay` twice, the cross-feed
    read and the in-loop multiply (`audiodsp_tank.c:537-538`, `:552`), and
    the loop one-pole once, so

        decay = min(10^(-3 k P / (2 T fs)) / sqrt|H(500 Hz)|,
                    10^(-3 k P / (2 x 1.5 T fs)))

    with P the mean half period in frames. The first term lifts `decay` by
    the one-pole's loss at 500 Hz; the second caps the bass (where the
    one-pole is 1) at 1.5 x T. Returns (decay, capped, t_lf): `t_lf` is the
    low-frequency T60 the handed decay gives, which bounds the tail."""
    a, b = half_periods(lines)
    p = 0.5 * (a + b)
    fs = float(sample_rate)
    mag = one_pole_mag(loop_hz, DECAY_HZ, fs)
    d = 10.0 ** (-3.0 * kappa * p / (2.0 * decay_s * fs)) / math.sqrt(mag)
    ceiling = 10.0 ** (-3.0 * kappa * p / (2.0 * LF_CAP * decay_s * fs))
    capped = d > ceiling
    if capped:
        d = ceiling
    if d > 0.999:
        d = 0.999
    if d < 0.0:
        d = 0.0
    if 0.0 < d < 1.0:
        t_lf = -3.0 * kappa * p / (2.0 * fs * math.log10(d))
    else:                               # pragma: no cover - never on the span
        t_lf = float("inf")
    return d, capped, t_lf


def tail_frames(sample_rate, predelay_ms, t_lf, size):
    """Tier 3's bound: ceil(fs x (Predelay + 1.6 x max(1.2 x T_lf,
    1.5 x Size)))."""
    longest = 1.2 * t_lf
    floor = 1.5 * size
    if floor > longest:
        longest = floor
    return int(math.ceil(sample_rate * (predelay_ms / 1000.0
                                        + 1.6 * longest)))


def _option(value, default):
    """A constructor option as a float; NaN is the option's default."""
    value = float(value)
    if value != value:
        return default
    return value


def _between(value, low, high):
    if value < low:
        return low
    if value > high:
        return high
    return value


class Reverb(_component.Component):
    """Dattorro's network as four machines: an EMT plate that is dense at
    once and darkens as Decay shortens, and a room, chamber and hall that
    build. The module docstring is the player's page."""

    NAME = 'Reverb'
    DISPLAY_NAME = 'Reverb'
    CATEGORIES = ('Reverb',)
    VERSION = '0.1.0'

    TIER = _component.AUDIODSP
    REQUIRES = ("audioverb",)

    CAPABILITIES = ()
    LATENCY_SAMPLES = 0
    TAIL_SAMPLES = None

    MACRO_LABELS = ("Character", "Decay", "Size", "Predelay", "Diffusion",
                    "Damping", "Bandwidth", "Low Cut", "Mod Depth",
                    "Mod Rate", "Width", "Tone", "Mix")
    MACRO_MODES = {
        0: "UNIPOLAR",
        1: "UNIPOLAR",
        2: "UNIPOLAR",
        3: "UNIPOLAR",
        4: "UNIPOLAR",
        5: "UNIPOLAR",
        6: "UNIPOLAR",
        7: "UNIPOLAR",
        8: "UNIPOLAR",
        9: "UNIPOLAR",
        10: "UNIPOLAR",
        11: "BIPOLAR",
        12: "UNIPOLAR",
    }
    _MACRO_RANGES = (
        (0.0, 4.0),                     # 0  Character, zone min(3, int(v))
        (0.3, 10.0, "log"),             # 1  Decay, T60 at 500 Hz, s
        (0.5, 1.5),                     # 2  Size, x the character's lines
        (0.0, MAX_PREDELAY_MS),         # 3  Predelay, ms
        (0.0, 0.9),                     # 4  Diffusion
        (500.0, 16000.0, "log"),        # 5  Damping, Hz
        (500.0, 20000.0, "log"),        # 6  Bandwidth, Hz
        (20.0, 500.0, "log"),           # 7  Low Cut, Hz
        (0.0, 2.0),                     # 8  Mod Depth, ms half swing
        (0.1, 5.0, "log"),              # 9  Mod Rate, Hz
        (0.0, 1.0),                     # 10 Width
        (-12.0, 12.0),                  # 11 Tone, dB end to end
        (0.0, 2.0),                     # 12 Mix; dry at unity to 1
    )

    #: `_component.macro_of` of the dossier's section 6 settings, Character
    #: at 0 / 42 / 85 / 127; patch 0 is the constructor's defaults on the
    #: grid.
    PATCHES = {
        0: ("Steel Plate",
            (0, 75, 64, 0, 106, 25, 109, 27, 17, 75, 127, 64, 22)),
        1: ("Short Plate",
            (0, 50, 64, 0, 106, 40, 115, 43, 13, 81, 114, 74, 19)),
        2: ("Damped Plate",
            (0, 44, 95, 0, 106, 12, 95, 55, 13, 75, 102, 48, 19)),
        3: ("Bass-Free Plate",
            (0, 65, 64, 0, 106, 25, 103, 114, 17, 75, 102, 74, 25)),
        4: ("Small Room",
            (42, 15, 25, 1, 85, 91, 103, 43, 13, 68, 102, 64, 16)),
        5: ("Live Room",
            (42, 44, 95, 3, 85, 102, 109, 36, 19, 63, 114, 74, 19)),
        6: ("Concert Hall",
            (127, 86, 95, 16, 99, 84, 100, 32, 32, 58, 127, 64, 22)),
        7: ("Dark Chamber",
            (85, 65, 64, 5, 99, 59, 86, 49, 19, 71, 102, 43, 20)),
        8: ("Bright Chamber",
            (85, 61, 64, 5, 99, 116, 119, 59, 19, 71, 102, 85, 20)),
        9: ("Slow Bloom",
            (127, 98, 127, 25, 113, 76, 95, 32, 64, 45, 127, 64, 29)),
    }

    def _build(self, character="plate", decay=2.4, size=1.0,
               predelay_ms=0.0, diffusion=0.75, damping_hz=1000.0,
               bandwidth_hz=12000.0, low_cut_hz=40.0, mod_depth_ms=0.27,
               mod_rate_hz=1.0, width=1.0, tone_db=0.0, mix=0.35,
               patch=None):
        if character == "spring":
            raise ValueError(
                "the spring character is parked: audioverb.Tank has no "
                "dispersive chain yet, so Reverb ships plate, room, chamber "
                "and hall")
        if character not in CHARACTERS:
            raise ValueError("character must be 'plate', 'room', 'chamber' "
                             "or 'hall'")
        index = CHARACTERS.index(character)
        self._tank = None
        self._lines = None
        self._taps = None
        self._index = index
        self._handed = {}
        self._capped = False
        self._t_lf = 0.0
        self._tail = 0
        #: True while several macros are applied at once (the constructor,
        #: `program_change`); the Tank is refreshed once, after the last, so
        #: a patch that moves Character and Size rebuilds it once.
        self._deferred = False
        spans = self._MACRO_RANGES
        values = [4.0 * CHARACTER_MIDI[index] / 127.0]
        options = (decay, size, predelay_ms, diffusion, damping_hz,
                   bandwidth_hz, low_cut_hz, mod_depth_ms, mod_rate_hz,
                   width, tone_db, mix)
        for macro, value in zip(range(1, 13), options):
            span = spans[macro]
            values.append(_between(_option(value, DEFAULTS[macro]),
                                   span[0], span[1]))
        self._deferred = True
        try:
            self._init_macros(tuple(values))
        finally:
            self._deferred = False
        self._refresh()
        if patch is not None:
            self.program_change(patch)

    # -- the maps ------------------------------------------------------

    def _value(self, index):
        return _component.macro_value(self._MACRO_RANGES[index],
                                      self._macros[index])

    def _character(self):
        """The zone Character's position sits in: 0 plate .. 3 hall."""
        zone = int(self._value(CHARACTER_I))
        if zone > HALL:
            return HALL
        if zone < PLATE:
            return PLATE
        return zone

    # -- hooks a planted fault overrides --------------------------------

    def _cut(self, index, size):
        """(lines, taps) the Tank is built on."""
        lines = line_set(index, size, self._sample_rate)
        return lines, tap_table(index, size, self._sample_rate, lines=lines)

    def _loop_hz(self, index, decay_s, damping):
        """The loop one-pole's corner: the damper law on the plate, the
        Damping setting elsewhere, clamped below Nyquist."""
        if index == PLATE:
            return self._hz(damper_hz(decay_s, damping, self._sample_rate))
        return self._hz(damping)

    def _decay(self, index, lines, decay_s, loop_hz):
        """(decay, capped, t_lf) by the Decay law."""
        return decay_law(KAPPA[index], lines, self._sample_rate, decay_s,
                         loop_hz)

    def _low_cut_hz(self, value):
        return self._hz(value)

    def _tone_db(self, value):
        """The tilt handed to the Tank, as set: the node keeps its tilt
        tracking at 0 dB (audiodsp#168)."""
        return value

    def _mod_rate_hz(self, value):
        return value

    def _mod_depth_ms(self, value, lines):
        del lines
        return value

    # -- applying ------------------------------------------------------

    def _apply_macro(self, index, position):
        del index, position
        if not self._deferred:
            self._refresh()

    def program_change(self, index, channel=0, note_id=-1,
                       sample_position=0):
        """Apply patch `index` whole, then refresh the Tank once, so a
        patch that moves Character and Size rebuilds it once."""
        self._deferred = True
        try:
            _component.Component.program_change(
                self, index, channel, note_id, sample_position)
        finally:
            self._deferred = False
        if type(self).PATCHES.get(index) is not None:
            self._refresh()

    def _refresh(self):
        fs = self._sample_rate
        index = self._character()
        size = _between(self._value(SIZE_I), 0.5, 1.5)
        lines, taps = self._cut(index, size)
        decay_s = _between(self._value(DECAY_I), 0.3, 10.0)
        loop = self._loop_hz(index, decay_s,
                             _between(self._value(DAMPING_I), 500.0,
                                      16000.0))
        decay, capped, t_lf = self._decay(index, lines, decay_s, loop)
        predelay = _between(self._value(PREDELAY_I), 0.0, MAX_PREDELAY_MS)
        handed = {
            "decay": decay,
            "diffusion": _between(self._value(DIFFUSION_I), 0.0, 0.9),
            "damping_hz": loop,
            "bandwidth_hz": self._hz(_between(self._value(BANDWIDTH_I),
                                              500.0, 20000.0)),
            "low_cut_hz": self._low_cut_hz(
                _between(self._value(LOW_CUT_I), 20.0, 500.0)),
            "predelay_ms": predelay,
            "mod_depth_ms": self._mod_depth_ms(
                _between(self._value(MOD_DEPTH_I), 0.0, 2.0), lines),
            "mod_rate_hz": self._mod_rate_hz(
                _between(self._value(MOD_RATE_I), 0.1, 5.0)),
            "drive": 0.0,
            "width": _between(self._value(WIDTH_I), 0.0, 1.0),
            "tone_db": self._tone_db(
                _between(self._value(TONE_I), -12.0, 12.0)),
            "mix": _between(self._value(MIX_I), 0.0, 2.0),
        }
        if self._tank is None:
            self._build_tank(index, lines, taps, handed)
        elif index != self._index or lines != self._lines \
                or taps != self._taps:
            self._recut(index, lines, taps, handed)
        else:
            self._tank.set(**handed)
        self._handed = handed
        self._capped = capped
        self._t_lf = t_lf
        self._tail = tail_frames(fs, predelay, t_lf, size)

    def _build_tank(self, index, lines, taps, handed):
        """Build the one Tank, at construction. Its sample rate, channel
        count and predelay allocation never change after, so every later
        Character or Size move is a re-cut of this node (`_recut`)."""
        tank = audioverb.Tank(
            sample_rate=self._sample_rate,
            channel_count=self._channel_count,
            max_predelay_ms=MAX_PREDELAY_MS,
            delays=lines,
            taps=taps,
            **handed)
        # `clear` empties every line and filter and keeps the source frames
        # the Tank has pulled and not yet played, so `reset()` does not skip
        # the dry; `audiocore.reset_buffer` would drop them.
        self._tank = self._own(tank, reset=tank.clear)
        self._index = index
        self._lines = lines
        self._taps = taps
        tank.play(self._source)
        self._output = tank

    def _recut(self, index, lines, taps, handed):
        """Re-cut the playing Tank in place (audiodsp#169): every line and
        filter starts empty, as a new Tank's would, and the source frames it
        holds stay, so the dry does not skip. The node allocates the new
        lines before it frees the old, and a refused allocation leaves it
        as it was."""
        self._tank.set(delays=lines, taps=taps, **handed)
        self._index = index
        self._lines = lines
        self._taps = taps

    @property
    def tail_samples(self):
        """Frames until the output is exactly zero once the input stops, as
        an upper bound (the dossier's Tier 3): the low-frequency T60 the
        handed `decay` gives, x 1.2 for the law's error, or 1.5 x Size for
        the character's own ringing, whichever is longer, x 1.6, plus the
        predelay."""
        self._check_live()
        return int(self._tail)
