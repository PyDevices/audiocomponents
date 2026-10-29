"""`soundfont` playing the rest of what a bank says, on `sf2_builder`'s
filter bank, and the SoundFont 2.04 default modulators.

Each trait is measured on what the instrument renders, with the bar beside
it:

- A region that doesn't use its filter plays unfiltered at every velocity
  (the voice gets no cutoff), and sounds the same brightness soft or hard.
- Velocity moves a filtered region's cutoff down to two octaves at
  velocity 0, and a soft note comes out darker. The brightness of a
  sawtooth through a plain low-pass goes about as the square root of the
  cutoff, so 1500 Hz against velocity 40's 581 Hz is about 4.1 dB; the
  6 dB resonance adds to it, and 5.1 dB was measured. The bar is 3.5 to
  6.5 dB.
- The modulation envelope sweeps the cutoff: the first tenth of a second is
  at least 6 dB brighter than the sustain, where the envelope has gone
  (8.6 dB measured).
- The mod wheel and channel pressure each add up to 50 cents of vibrato to
  the region's own, on held notes and new ones, and the output's pitch then
  swings at least 60 cents peak to peak (88 measured, through 20 ms
  windows) where it held within 5 (2.4 measured).
- Control Change 7 and 11 each scale the level by the square of their
  fraction: Expression at 64 is 11.9 dB under 127, within 0.2 dB.

The brightness measure is the RMS of the first difference over the RMS,
in dB, which takes level out.

A fault planted to show these can fail (2026-10-29): velocity to cutoff
with its sign turned (`velocity / 127.0` for `1.0 - velocity / 127.0`)
failed the velocity, brightness and sweep traits; Control Change 7 and 11
on a straight line rather than the square failed the level trait.
"""

import math
import os
import pathlib
import shutil
import sys
import tempfile
import unittest

import audioinstruments
import audioinstruments.soundfont as soundfont

SUPPORT = pathlib.Path(__file__).resolve().parent / "support"
if str(SUPPORT) not in sys.path:
    sys.path.insert(0, str(SUPPORT))

import sf2_builder  # noqa: E402
import sf2_play  # noqa: E402

SR = 48000
OPEN, FILTERED, SWEPT, LFOS = 0, 1, 2, 3


def brightness_db(values):
    """RMS of the first difference over the RMS, in dB."""
    diff = [values[i] - values[i - 1] for i in range(1, len(values))]
    return 20.0 * math.log10(sf2_play.rms(diff) / sf2_play.rms(values))


def pitch_swing_cents(values, window=960):
    """Peak-to-peak pitch over `values`, in cents, from rising zero
    crossings counted in `window`-frame windows."""
    rates = []
    for start in range(0, len(values) - window, window):
        chunk = values[start:start + window]
        crossings = [i for i in range(1, window)
                     if chunk[i - 1] < 0 <= chunk[i]]
        if len(crossings) > 2:
            rates.append((len(crossings) - 1)
                         / float(crossings[-1] - crossings[0]))
    return 1200.0 * math.log2(max(rates) / min(rates))


class SoundFontModulationTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp(prefix="sf2mod")
        cls.path = os.path.join(cls.tmp, "filter.sf2")
        sf2_builder.filter_bank().write(cls.path)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def setUp(self):
        self.inst = audioinstruments.create("soundfont", SR, bank=self.path)

    def tearDown(self):
        self.inst.deinit()

    def voice(self, key=60):
        slot = self.inst._player.held[(0, key)][0]
        return self.inst.output.voice[slot]

    def play(self, program, velocity, seconds, key=60):
        self.inst.program_change(program)
        self.inst.note_on(key, velocity)
        out = sf2_play.render(self.inst, seconds, channel=0)
        self.inst.note_off(key)
        sf2_play.render(self.inst, 0.3)
        return out

    def test_an_open_region_is_never_filtered(self):
        self.inst.program_change(OPEN)
        for velocity in (127, 30):
            self.inst.note_on(60, velocity)
            self.assertIsNone(self.voice().cutoff)
            self.inst.note_off(60)
        hard = brightness_db(self.play(OPEN, 127, 0.3)[4800:])
        soft = brightness_db(self.play(OPEN, 30, 0.3)[4800:])
        self.assertAlmostEqual(hard, soft, delta=0.1)

    def test_velocity_moves_the_cutoff(self):
        self.inst.program_change(FILTERED)
        for velocity in (127, 64, 1):
            self.inst.note_on(60, velocity)
            expected = 1500.0 * 2.0 ** (-2.0 * (1.0 - velocity / 127.0))
            self.assertAlmostEqual(self.voice().cutoff, expected,
                                   delta=expected * 0.005)
            self.inst.note_off(60)

    def test_velocity_changes_brightness(self):
        hard = brightness_db(self.play(FILTERED, 127, 0.3)[4800:])
        soft = brightness_db(self.play(FILTERED, 40, 0.3)[4800:])
        self.assertGreater(hard - soft, 3.5)
        self.assertLess(hard - soft, 6.5)

    def test_modulation_envelope_sweeps_the_cutoff(self):
        out = self.play(SWEPT, 127, 1.2)
        early = brightness_db(out[480:4800])
        late = brightness_db(out[48000:57600])
        self.assertGreater(early - late, 6.0)

    def test_wheel_and_pressure_add_vibrato(self):
        self.inst.program_change(LFOS)
        self.inst.note_on(60, 100)
        voice = self.voice()
        self.assertAlmostEqual(voice.vibrato_depth, 30.0)
        self.inst.control_change(1, 127)
        self.assertAlmostEqual(voice.vibrato_depth, 80.0)
        self.inst.channel_pressure(127)
        self.assertAlmostEqual(voice.vibrato_depth, 130.0)
        self.inst.control_change(1, 0)
        self.assertAlmostEqual(voice.vibrato_depth, 80.0)
        self.inst.note_on(64, 100)
        self.assertAlmostEqual(self.voice(64).vibrato_depth, 80.0)
        self.inst.channel_pressure(0)
        self.assertAlmostEqual(voice.vibrato_depth, 30.0)

    def test_wheel_vibrato_is_heard(self):
        steady = pitch_swing_cents(self.play(OPEN, 100, 0.6))
        self.inst.control_change(1, 127)
        swung = pitch_swing_cents(self.play(OPEN, 100, 0.6))
        self.assertLess(steady, 5.0)
        self.assertGreater(swung, 60.0)

    def test_volume_and_expression_go_as_the_square(self):
        full = sf2_play.rms(self.play(OPEN, 100, 0.2)[2400:])
        self.inst.control_change(11, 64)
        half = sf2_play.rms(self.play(OPEN, 100, 0.2)[2400:])
        expected = 40.0 * math.log10(64 / 127.0)
        self.assertAlmostEqual(20.0 * math.log10(half / full), expected,
                               delta=0.2)
        # A held note follows, and Volume's default of 100 is in the level.
        self.inst.control_change(11, 127)
        self.inst.note_on(60, 100)
        voice = self.voice()
        default = voice.level
        self.inst.control_change(7, 127)
        self.assertAlmostEqual(default / voice.level, (100 / 127.0) ** 2,
                               places=5)
        self.inst.reset()
        self.assertEqual(self.inst._player.volume_cc, {})

    def test_bank_modulator_defaults_are_the_specifications(self):
        self.assertEqual(soundfont.VELOCITY_TO_CUTOFF, -2400)
        self.assertEqual(soundfont.MOD_WHEEL_TO_VIBRATO, 50.0)
        self.assertEqual((soundfont.DEFAULT_VOLUME,
                          soundfont.DEFAULT_EXPRESSION), (100, 127))


if __name__ == "__main__":
    unittest.main()
