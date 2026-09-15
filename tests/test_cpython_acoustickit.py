"""acoustickit: the traits that make it a drum kit rather than a drum machine.

`tests/test_cpython_instruments.py` already walks every instrument in `ALL`
and checks the contract - metadata, patches, that every mapped note sounds and
every unmapped one does not. What is left for here is the behaviour this
instrument exists for, which no contract test would notice was missing.

## The traits, with their bars

| ID | Trait | Bar |
|---|---|---|
| A1 | Striking harder makes a drum brighter, not just louder | monotonic over 5 velocities, 35-127 |
| A2 | The kick's brightness range is wide enough to hear | >= 3x from softest to hardest |
| A3 | No two strikes of the same drum are identical | any difference |
| A4 | Consecutive strikes stay within a bounded envelope | peak/pitch <= 4%, centroid <= 6% |
| A5 | Closing the hi-hat chokes an open one | exact silence |
| A6 | Nothing else in the kit chokes anything | ringing survives |
| A7 | A drum's decay outlives the strike that made it | >= 20 blocks |
| A8 | Eight voices at once do not clip | no sample at the rail |
| A9 | The snare's early peak is its second mode, not its first | 300-360 Hz |

A3 and A4 are one claim in two halves, and the second half is what makes the
first honest: a drum that varied *without* a bound would be a broken drum
rather than a lively one. The mechanism is `_JITTER`, and it is the whole of
what a sample library buys with round-robin captures.

A9 is the one trait here that is graded against a real measurement rather than
against design intent. Skrodzka, Hojan & Proksza (2006) put a 14" snare's
(0,1) mode at 224 Hz damping at 5.07% and its (1,1) at 322 Hz damping at
1.10%, so the fundamental is gone in about a tenth of a second while the mode
above it rings three times longer. The audible pitch of a snare is therefore
*not* its fundamental, and a model built on the usual "decay falls off with
frequency" assumption would land this at 224 Hz and be wrong in a way nobody
would catch by listening for a bug. See the dossier in the workspace anchor,
`docs/effects-internal/dossiers/instruments/acoustickit.md`.

## The planted faults

`docs/correctness-standard.md` in audioif: "a trait without a planted fault is
not a check; it is a hope." Each of these was made and reverted:

| Fault | Breaks | What was measured |
|---|---|---|
| `tilt` forced to 0.0 for every mode | A1, A2 | every drum flat across velocity; kick spread 4.51x -> 1.00x |
| `_JITTER = 0.0` | A3 | four consecutive snares byte-identical |
| `_JITTER = 0.5` | A4 | snare wanders 40% of peak hit to hit, and detunes audibly |
| `hat_bank.clear()` removed from `strike` | A5 | open hat rings under the closed one, 5944 peak where there should be silence |
| hi-hat moved into the main bank | A5, A6 | choking the hat takes the kick and the crash with it |
"""

import sys
import unittest

import numpy as np

import audiocore

sys.path.insert(0, "lib")
import audioinstruments as ai                                   # noqa: E402

SR = 48000

#: Five velocities from soft to hard, and the softest is 35 rather than 20 for
#: a measurement reason. A tom at velocity 20 peaks at -35 dBFS, which puts its
#: high modes down where int16 quantisation noise lives - and quantisation
#: noise is white, so it *raises* a measured centroid. Three drums then read
#: brighter at velocity 20 than at 45 and A1 failed on an artefact of the
#: quantiser rather than anything the instrument did. Nobody judges a drum's
#: brightness 35 dB down either.
VELOCITIES = (35, 60, 85, 105, 127)


def render(instrument, blocks):
    out = []
    for _ in range(blocks):
        data = bytes(audiocore.get_buffer(instrument.output)[1])
        out.append(np.frombuffer(data, dtype="<i2").astype(float))
    return np.concatenate(out)


def struck(pitch, velocity, blocks=20):
    instrument = ai.create("acoustickit", SR, 2)
    instrument.note_on(pitch, velocity)
    return render(instrument, blocks)


def left(samples):
    """The left channel. Everything here renders stereo, and a spectrum taken
    over the interleaved stream reads every frequency at half of what it is."""
    return samples[0::2]


def _window(samples, ms):
    """A window of the left channel starting at the ONSET, not at sample 0.

    The first pull through a fresh graph primes the splitter and the mixer, so
    the first strike of a new instrument begins about a block later than every
    strike after it. Measured from sample 0 that shifts a 25 ms window across
    5.3 ms of leading silence and reads the first hit of any kit 700 Hz
    brighter than the rest - which looks exactly like a real defect, and is
    not. Aligning to the onset is also what `.reference-captures/lufs.py` does,
    for the same reason.
    """
    channel = left(samples)
    n = int(SR * ms / 1000.0)
    loud = np.abs(channel)
    threshold = np.max(loud) * 0.02 if len(loud) else 0.0
    onset = int(np.argmax(loud > threshold)) if threshold > 0 else 0
    segment = channel[onset:onset + n]
    if len(segment) < n:
        segment = np.pad(segment, (0, n - len(segment)))
    spectrum = np.abs(np.fft.rfft(segment * np.hanning(len(segment))))
    return spectrum, np.fft.rfftfreq(len(segment), 1.0 / SR)


def centroid(samples, ms=25.0):
    spectrum, freqs = _window(samples, ms)
    total = np.sum(spectrum)
    return float(np.sum(freqs * spectrum) / total) if total else 0.0


def dominant(samples, ms=120.0, low=60.0):
    spectrum, freqs = _window(samples, ms)
    spectrum[freqs < low] = 0.0
    return float(freqs[int(np.argmax(spectrum))])


def peak(samples):
    return float(np.max(np.abs(samples)))


DRUMS = (("kick", 36), ("snare", 38), ("low floor tom", 41),
         ("hi-mid tom", 48), ("closed hat", 42), ("crash", 49))


class AcousticKitTraits(unittest.TestCase):

    def test_a1_harder_is_brighter_on_every_drum(self):
        for name, pitch in DRUMS:
            with self.subTest(drum=name):
                cents = [centroid(struck(pitch, v)) for v in VELOCITIES]
                for softer, louder in zip(cents, cents[1:]):
                    self.assertGreater(
                        louder, softer,
                        "%s: centroid did not rise, %s" % (name, cents))

    def test_a2_the_kicks_brightness_range_is_audible(self):
        cents = [centroid(struck(36, v)) for v in VELOCITIES]
        self.assertGreaterEqual(cents[-1] / cents[0], 3.0,
                                "kick spread only %.2fx" % (cents[-1] / cents[0]))

    def test_a3_no_two_strikes_are_identical(self):
        """Each strike rings out completely before the next.

        Written without the rest, this passed with the jitter turned off -
        which makes it a hope rather than a check. Strikes landing on each
        other's tails differ for that reason alone, so what it was measuring
        was that a snare rings, not that two snares differ. The first strike
        is discarded as well: a fresh graph primes on its first pull and
        begins a block later than every strike after it.
        """
        instrument = ai.create("acoustickit", SR, 2)
        takes = []
        for _ in range(5):
            instrument.note_on(38, 100)
            takes.append(render(instrument, 40))
            render(instrument, 600)          # ring out, to exact silence
        takes = takes[1:]
        shortest = min(len(take) for take in takes)
        for index in range(1, len(takes)):
            self.assertFalse(
                np.array_equal(takes[0][:shortest], takes[index][:shortest]),
                "strike %d was identical to the one before it" % (index + 2))

    def test_a4_but_they_stay_within_a_bounded_envelope(self):
        """Bounded is a claim about how it SOUNDS, not about samples.

        Two strikes a fifth of a semitone apart diverge completely sample by
        sample within a few cycles - that is what a phase difference is, and
        measuring it would only be measuring the jitter's existence. What has
        to stay put is what the ear actually reads off a drum: how loud it
        was, how bright it was, and what pitch it was.
        """
        # One instrument, because the jitter advances per strike and a fresh
        # instrument would restart its sequence - but each strike is let ring
        # out before the next. Landing a snare on the tail of the last one is
        # a real and audible difference (the first hit reads 700 Hz brighter,
        # because the tail underneath it has no attack modes left), and it is
        # not the thing this trait is about.
        instrument = ai.create("acoustickit", SR, 2)
        takes = []
        for _ in range(6):
            instrument.note_on(38, 100)
            takes.append(render(instrument, 40))
            render(instrument, 80)           # ~0.4 s, past the snare's T60
        # The centroid's bar is looser than the others because it is a
        # weighted mean over modes that each moved independently, so a 1.2%
        # jitter per mode lands as a few percent on the sum. `_JITTER = 0.5`
        # puts it past 40%, which is what the bar has to catch.
        for name, measure, bar in (("peak", peak, 0.04),
                                   ("centroid", centroid, 0.06),
                                   ("pitch", dominant, 0.03)):
            values = [measure(take) for take in takes]
            spread = (max(values) - min(values)) / max(values)
            self.assertLess(spread, bar,
                            "%s wandered %.1f%% across six strikes: %s"
                            % (name, 100 * spread,
                               ["%.1f" % v for v in values]))

    def test_a5_closing_the_hi_hat_chokes_an_open_one(self):
        instrument = ai.create("acoustickit", SR, 2)
        instrument.note_on(46, 110)
        render(instrument, 2)
        instrument.note_on(42, 90)
        tail = render(instrument, 40)
        # Well after the closed hat itself has died, there must be nothing
        # left of the open one.
        late = tail[len(tail) // 2:]
        self.assertEqual(float(np.max(np.abs(late))), 0.0)

    def test_a6_nothing_else_in_the_kit_chokes_anything(self):
        """The crash has to survive being played over, not merely leave
        something audible behind.

        The first version of this asserted "output is not silent" after a bar
        of drums over a crash, which the *last* drum struck satisfies all by
        itself - it passed while a kick was in fact cutting the crash dead,
        7584 peak to 61. It has to be the crash's own level that is compared.
        """
        alone = ai.create("acoustickit", SR, 2)
        alone.note_on(49, 110)
        render(alone, 10)
        crash_only = peak(render(alone, 20))

        under = ai.create("acoustickit", SR, 2)
        under.note_on(49, 110)
        render(under, 10)
        under.note_on(36, 5)                 # a kick too quiet to explain it
        with_kick = peak(render(under, 20))

        self.assertGreater(
            with_kick, crash_only * 0.5,
            "a near-silent kick cut the crash from %.0f to %.0f"
            % (crash_only, with_kick))

    def test_a7_a_drum_outlives_the_strike_that_made_it(self):
        for name, pitch in (("kick", 36), ("low floor tom", 41),
                            ("crash", 49), ("ride", 51)):
            with self.subTest(drum=name):
                instrument = ai.create("acoustickit", SR, 2)
                instrument.note_on(pitch, 110)
                alive = 0
                for index in range(200):
                    if np.max(np.abs(render(instrument, 1))) > 0.0:
                        alive = index
                self.assertGreaterEqual(alive, 20,
                                        "%s died after %d blocks" % (name, alive))

    def test_a8_eight_voices_at_once_do_not_clip(self):
        """Eight is the polyphony this kit is built for, and a drummer with
        two hands and two feet cannot reach more than about five. All fourteen
        at full velocity does clip, and that is left as a known ceiling rather
        than paid for with headroom the whole kit would then lack."""
        instrument = ai.create("acoustickit", SR, 2)
        for pitch in (36, 38, 41, 45, 47, 48, 49, 51):
            instrument.note_on(pitch, 127)
        samples = render(instrument, 40)
        self.assertLess(float(np.max(np.abs(samples))), 32767.0,
                        "eight voices clipped")

    def test_a9_the_snares_early_peak_is_its_second_mode(self):
        # 322 Hz, not the 224 Hz fundamental: the measured damping kills the
        # fundamental three times faster than the mode above it.
        self.assertTrue(300.0 <= dominant(struck(38, 100)) <= 360.0,
                        "snare read %.1f Hz" % dominant(struck(38, 100)))


if __name__ == "__main__":
    unittest.main()
