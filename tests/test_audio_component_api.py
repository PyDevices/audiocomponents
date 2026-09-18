import array
import math
import sys
import unittest

import audiocore
import audioeffects
import audioinstruments
from audioeffects import _component
from audioeffects import _core
from audioeffects import rebuilt


#: `_check_metadata` reads this off the defining module.
VENDOR = "PyDevices"

COMMON = ("set_macro", "program_change", "get_macro", "reset", "deinit")
INSTRUMENT = ("note_on", "note_off", "all_notes_off", "pitch_bend",
              "control_change", "channel_pressure", "poly_pressure")
EFFECT = ("pitch_bend", "control_change", "channel_pressure",
          "poly_pressure")


def source(channels=2):
    return audiocore.RawSample(
        array.array("h", [0] * 256 * channels), sample_rate=48000,
        channel_count=channels)


class AudioComponentApiTests(unittest.TestCase):
    def check_common(self, component, methods, channels=2):
        for name in COMMON + methods:
            self.assertTrue(callable(getattr(component, name)), name)
        self.assertEqual(component.sample_rate, 48000)
        self.assertEqual(component.channel_count, channels)
        self.assertGreaterEqual(component.latency_samples, 0)
        self.assertTrue(component.tail_samples is None or
                        component.tail_samples >= 0)
        self.assertIsInstance(component.capabilities, tuple)
        self.assertEqual(component.patch_index, 0)
        self.assertEqual(len(component.output._get_buffer()[1]) %
                         (2 * channels), 0)

    def test_discovery_lists_are_stable(self):
        self.assertEqual(audioinstruments.ALL,
                         tuple(dict.fromkeys(audioinstruments.ALL)))
        self.assertEqual(audioeffects.ALL,
                         tuple(sorted(audioeffects.ALL)))
        self.assertEqual(len(audioinstruments.ALL), 55)
        self.assertEqual(len(audioeffects.ALL), 45)

    def test_all_instruments_implement_live_surface(self):
        for name in audioinstruments.ALL:
            with self.subTest(name=name):
                component = audioinstruments.create(name, 48000)
                try:
                    self.check_common(component, INSTRUMENT)
                    if component.macro_labels:
                        component.set_macro(0, 64)
                        self.assertIsNone(component.patch_index)
                        component.program_change(0)
                        self.assertEqual(component.patch_index, 0)
                    component.note_on(60, 100, note_id=22,
                                     sample_position=3)
                    component.note_off(60, note_id=22, sample_position=7)
                    component.all_notes_off()
                    component.reset()
                finally:
                    component.deinit()
                    component.deinit()
                with self.assertRaises(RuntimeError):
                    _ = component.output

    def test_all_effects_preserve_mono_and_implement_live_surface(self):
        for name in audioeffects.ALL:
            with self.subTest(name=name):
                component = audioeffects.create(name, source(1), 48000)
                try:
                    self.check_common(component, EFFECT, channels=1)
                    labels = getattr(component, "MACRO_LABELS", ())
                    if labels:
                        component.set_macro(0, 64, sample_position=3)
                        self.assertIsNone(component.patch_index)
                        component.program_change(0, sample_position=7)
                    else:
                        with self.assertRaises(IndexError):
                            component.get_macro(0)
                    component.pitch_bend(8192, sample_position=2)
                    component.control_change(1, 64, sample_position=2)
                    component.channel_pressure(64, sample_position=2)
                    component.poly_pressure(60, 64, sample_position=2)
                    component.reset()
                finally:
                    component.deinit()
                    component.deinit()
                with self.assertRaises(RuntimeError):
                    _ = component.output

    def test_invalid_construction_and_control_values_are_explicit(self):
        with self.assertRaises(ValueError):
            audioinstruments.create("minimoog", 48000, channel_count=3)
        with self.assertRaises(ValueError):
            audioeffects.create("LowPass", source(1), 44100)
        component = audioinstruments.create("minimoog", 48000)
        try:
            with self.assertRaises(IndexError):
                component.set_macro(99, 0)
            with self.assertRaises(ValueError):
                component.note_on(128)
            with self.assertRaises(ValueError):
                component.pitch_bend(16384)
            # MIDI scalar controls clamp instead of rejecting host automation
            # overshoot, while the patch index itself remains an ignored wire
            # message when unknown.
            component.set_macro(0, 1000)
            self.assertEqual(component.get_macro(0), 127.0)
            component.program_change(999)
        finally:
            component.deinit()

    def test_note_identity_and_zero_velocity_follow_midi_rules(self):
        component = audioinstruments.create("minimoog", 48000)
        try:
            component.note_on(60, 100, note_id=10)
            component.note_on(60, 100, note_id=11)
            self.assertEqual(len(component._active), 2)
            component.note_off(60, note_id=10)
            self.assertEqual(len(component._active), 1)
            # A note-off for an unrelated identity must not release note 11.
            component.note_off(61, note_id=99)
            self.assertEqual(len(component._active), 1)
            # MIDI's zero-velocity note-on is the other spelling of note-off.
            component.note_on(60, 0, note_id=11)
            self.assertEqual(len(component._active), 0)
        finally:
            component.deinit()


# --------------------------------------------------------------------------
# Tier 1: what a constructor `patch=` may cost
# --------------------------------------------------------------------------

#: A probe longer than the render, so a class that loses a block has a
#: block left to ask for and the count below discriminates.
PATCH_PROBE_FRAMES = 4096
PATCH_RENDER_FRAMES = 1024
PATCH_BLOCK = 256


class CountingSource:
    """The borrowed source, counting the frames a class takes from it."""

    def __init__(self, frames=PATCH_PROBE_FRAMES, channels=2, rate=48000,
                 block=PATCH_BLOCK):
        self.sample_rate = int(rate)
        self.channel_count = int(channels)
        self.bits_per_sample = 16
        self.samples_signed = True
        self.frames = 0
        amplitude = 0.5 * 32767.0
        data = array.array("h")
        for i in range(frames):
            value = int(round(amplitude * math.sin(
                2.0 * math.pi * 1000.0 * i / rate)))
            for _ in range(channels):
                data.append(value)
        self._pcm = memoryview(data.tobytes())
        self._stride = int(block) * self.channel_count * 2
        self._position = 0

    def _reset_buffer(self, single_channel_output=False, audio_channel=0):
        self._position = 0

    def _get_buffer(self, single_channel_output=False, audio_channel=0):
        chunk = bytes(self._pcm[self._position:self._position + self._stride])
        self._position += len(chunk)
        self.frames += len(chunk) // (2 * self.channel_count)
        return (1 if self._position < len(self._pcm) else 0,
                memoryview(chunk))


def patch_classes():
    """Every effect class a host can construct, rebuilt or shipped.

    `audioeffects.ALL` is what the library serves; `rebuilt.module_class`
    is what this program has rebuilt but not yet adopted, and a phase's
    classes live there for the whole of the phase. Both are walked so a
    class is covered from the day it is written rather than the day it is
    adopted.
    """
    found = []
    for name in audioeffects.ALL:
        cls = getattr(audioeffects, name, None)
        if cls is not None:
            found.append((name, cls))
    for name in rebuilt.known():
        cls = rebuilt.module_class(name)
        if cls is not None and not any(cls is known for _, known in found):
            found.append(("rebuilt " + name, cls))
    return found


def source_cost(cls, **options):
    """The frames `cls` takes from its source to render a fixed length."""
    counter = CountingSource()
    effect = cls.create(counter, 48000, **options)
    try:
        want = PATCH_RENDER_FRAMES * counter.channel_count * 2
        got = 0
        while got < want:
            _, data = audiocore.get_buffer(effect.output)
            if not len(data):
                break
            got += len(data)
    finally:
        effect.deinit()
    return counter.frames


class PrimesTwiceUnderAPatch(_component.Component):
    """audiocomponents#82's behaviour, planted.

    A class that re-primes from `_apply_macro` while `_build` is still
    running, and primes again when `_build` finishes - which is what
    `Distortion` did at its four scoop patches, where the Character macro
    crosses 0.5 and the graph is rebuilt. The first priming pull's block
    of the borrowed source is thrown away, so the class starts 5.3 ms into
    the material.
    """

    NAME = "PrimesTwiceUnderAPatch"
    TIER = _component.STOCK
    LATENCY_SAMPLES = 0
    TAIL_SAMPLES = 0
    CAPABILITIES = ()
    MACRO_LABELS = ("Mix",)
    MACRO_MODES = {0: "UNIPOLAR"}
    _MACRO_RANGES = ((0.0, 1.0),)
    #: Patch 0 leaves the knob where the constructor put it, so the seeding
    #: pass crosses nothing; patch 1 pushes it over the boundary, which is
    #: the shape of a Character macro that rebuilds the graph.
    PATCHES = {0: ("As built", (0,)), 1: ("Rewires", (127,))}
    #: Set to False to take the same class without the fault.
    PLANTED = True

    def _build(self, mix=0.0, patch=None):
        import audiomixer
        self._mixer = self._own(
            audiomixer.Mixer(voice_count=1, **self._pcm(1024)), reset=False)
        self._output = self._mixer
        self._rewired = False
        self._init_macros((mix,), patch)
        self._prime()

    def _prime(self):
        self._mixer.voice[0].play(self._source)

    def _apply_macro(self, index, position):
        del index
        self._mixer.voice[0].level = max(0.0, min(1.0, position))
        rewire = position >= 0.5
        if rewire == self._rewired:
            return
        self._rewired = rewire
        if type(self).PLANTED or not self._constructing:
            # The fault: `_build` primes once more when it returns, so this
            # pull's block of the borrowed source is dropped.
            self._prime()


class WithoutTheFault(PrimesTwiceUnderAPatch):
    NAME = "WithoutTheFault"
    PLANTED = False


class AConstructorPatchCostsTheSourceNothing(unittest.TestCase):
    """Tier 1, audiocomponents#82.

    Handing `patch=N` to the constructor must not cost the class a frame
    of the borrowed source that building without it would have kept. A
    class that primes twice - once while `_init_macros` applies the patch
    from inside `_build`, once when `_build` finishes - throws the first
    pull's block away, and its output starts that far into the material.

    The frames taken from the source is the reading rather than the
    onset, because it is exact on every class and no signal can fool it.
    An onset read as the first sample above a fraction of the render's own
    peak cannot do this job: a bias macro landing beside its span centre
    rather than on it gives the class a DC settling prologue out of
    silence, and the threshold fires on that while the material has not
    moved at all. That is what #82's first table was reading. (When this was
    written the centre of a bipolar span was 63.5 and unreachable;
    `ABipolarMacroHasACentreDetent` below is why it is MIDI 64 now.)
    """

    @staticmethod
    def overspend(cls):
        """`[(patch, frames, frames_without_a_patch), ...]`, empty if the
        class holds the law. Not an assertion, so the planted-fault test
        below can read the same walk and require it to be non-empty."""
        base = source_cost(cls)
        rows = []
        for index in sorted(cls.PATCHES):
            frames = source_cost(cls, patch=index)
            if frames != base:
                rows.append((index, frames, base))
        return rows

    def check(self, cls, name):
        self.assertEqual(
            self.overspend(cls), [],
            "%s built with a constructor patch takes a different amount of "
            "its source than the same class built without one; the rows are "
            "(patch, frames, frames without a patch)" % name)

    def test_every_class_that_takes_a_patch_holds_the_law(self):
        checked = 0
        for name, cls in patch_classes():
            if not getattr(cls, "PATCHES", None):
                continue
            try:
                cls.create(CountingSource(), 48000, patch=0).deinit()
            except TypeError:
                # Nine shipped classes that were never rebuilt take no
                # constructor `patch=` at all, and neither do the stock
                # twins the Phase 4 rebuilds will replace
                # (audiocomponents#84). Every class that does take one is
                # held to the law.
                continue
            with self.subTest(name=name):
                self.check(cls, name)
            checked += 1
        self.assertGreater(checked, 20, "the walk found almost no classes")

    def test_every_rebuilt_class_takes_a_constructor_patch(self):
        for name in rebuilt.known():
            cls = rebuilt.module_class(name)
            if cls is None or not getattr(cls, "PATCHES", None):
                continue
            with self.subTest(name=name):
                effect = cls.create(CountingSource(), 48000, patch=0)
                try:
                    self.assertEqual(effect.patch_index, 0)
                finally:
                    effect.deinit()

    def test_planted_fault_a_second_priming_pull_is_red(self):
        # The same fixture without the fault is green, so what turns the
        # law red below is the double priming and not the fixture.
        self.assertEqual(self.overspend(WithoutTheFault), [])
        self.assertEqual(source_cost(WithoutTheFault, patch=1),
                         source_cost(WithoutTheFault))
        # And the fault only bites under a patch: built without one, the
        # planted class costs exactly what the clean one costs.
        self.assertEqual(source_cost(PrimesTwiceUnderAPatch),
                         source_cost(WithoutTheFault))
        self.assertEqual(
            self.overspend(PrimesTwiceUnderAPatch),
            [(1, PATCH_RENDER_FRAMES + PATCH_BLOCK, PATCH_RENDER_FRAMES)],
            "the planted double priming cost the source nothing, so the law "
            "above cannot fail")
        with self.assertRaises(AssertionError):
            self.check(PrimesTwiceUnderAPatch, "PrimesTwiceUnderAPatch")


class CentresOnTheOldLaw(_component.Component):
    """audiocomponents#87's behaviour, planted.

    A class that crosses the 0-127 grid the way every class did before the
    detent landed: position = midi / 127, which puts a bipolar macro's MIDI
    64 at 0.50394 of its span. On a symmetric span that is +0.007874 rather
    than 0, which is the bias `Overdrive` and `Fuzz` sent into their shapers
    from patches whose name says "centred".
    """

    NAME = "CentresOnTheOldLaw"
    TIER = _component.STOCK
    LATENCY_SAMPLES = 0
    TAIL_SAMPLES = 0
    CAPABILITIES = ()
    MACRO_LABELS = ("Bias",)
    MACRO_MODES = {0: "BIPOLAR"}
    _MACRO_RANGES = ((-1.0, 1.0),)
    PATCHES = {0: ("Centred", (64,)), 1: ("Hard left", (0,))}
    #: Set to False to take the same class without the fault.
    PLANTED = True

    def _build(self, bias=0.0, patch=None):
        self._output = self._source
        self._init_macros((bias,), patch)

    def _apply_macro(self, index, position):
        del index, position

    def set_macro(self, index, value, channel=0, note_id=-1,
                  sample_position=0):
        if not type(self).PLANTED:
            return _component.Component.set_macro(
                self, index, value, channel, note_id, sample_position)
        self._macros[index] = min(1.0, max(0.0, float(value) / 127.0))
        self._patch_index = None

    def program_change(self, index, channel=0, note_id=-1,
                       sample_position=0):
        if not type(self).PLANTED:
            return _component.Component.program_change(
                self, index, channel, note_id, sample_position)
        patch = type(self).PATCHES.get(index)
        if patch is None:
            return
        for macro, value in enumerate(patch[1]):
            self._macros[macro] = min(1.0, max(0.0, float(value) / 127.0))
        self._patch_index = index


class CentresOnTheNewLaw(CentresOnTheOldLaw):
    NAME = "CentresOnTheNewLaw"
    PLANTED = False


class ABipolarMacroHasACentreDetent(unittest.TestCase):
    """Tier 1, audiocomponents#87.

    A BIPOLAR macro's centre is the setting that means "none of this", and
    MIDI 64 is the centre detent on every controller a musician owns. The
    0-127 grid has an even number of steps and so no middle of its own -
    64/127 is 0.50394 - so until the detent landed no patch could ask for
    the centre of a bipolar span. `Overdrive`'s Symmetry at MIDI 64 was
    +0.007874 rather than 0: a bias the shaper turned into DC that never
    decayed, so all eight shipped patches held +56 to +85 LSB (patch 6
    +4469, -17.3 dBFS) forever and `TAIL_SAMPLES = 512` was false at every
    one of them. `Fuzz`'s patch 0, whose name is "Bias centred", banged 329
    LSB out of digital silence, and `Saturation`'s patch 4 thumped 9067.

    The law is `_component.position_of_midi`, and it is one law for every
    path in and out - constructor default, `set_macro`, `program_change`,
    `macro()`, `get_macro()` and `macro_of()` patch authoring - so a class
    needs nothing of its own. These rows walk every class that has a
    bipolar macro, at the grid values whose meaning is fixed: 64 is the
    span's centre, 0 and 127 are its ends, and a patch that holds 64 gets
    the centre and not something 1/127 away from it.
    """

    #: The grid values whose meaning the law fixes exactly, as
    #: `(midi, which end of the span)`. Everything between them is a taste
    #: call; these three are not.
    ANCHORS = ((0, "low"), (64, "centre"), (127, "high"))

    @staticmethod
    def anchors_missed(cls):
        """`[(kind, index, midi, read, wanted), ...]`, empty if the class
        holds the law. Not an assertion, so the planted-fault test below can
        read the same walk and require it to be non-empty."""
        modes = getattr(cls, "MACRO_MODES", None) or {}
        bipolar = [index for index in sorted(modes)
                   if modes[index] == "BIPOLAR"]
        if not bipolar:
            return []
        rows = []
        effect = cls.create(CountingSource(), 48000)
        try:
            for index in bipolar:
                span = cls._MACRO_RANGES[index]
                wanted = {"low": span[0], "high": span[1],
                          "centre": (span[0] + span[1]) / 2.0}
                for midi, which in ABipolarMacroHasACentreDetent.ANCHORS:
                    effect.set_macro(index, midi)
                    read = effect.macro(index)
                    if read != wanted[which]:
                        rows.append(("set_macro", index, midi, read,
                                     wanted[which]))
                    back = effect.get_macro(index)
                    if back != midi:
                        rows.append(("get_macro", index, midi, back, midi))
                for patch in sorted(cls.PATCHES):
                    value = cls.PATCHES[patch][1][index]
                    if value not in (0, 64, 127):
                        continue
                    effect.program_change(patch)
                    read = effect.macro(index)
                    which = {0: "low", 64: "centre", 127: "high"}[value]
                    if read != wanted[which]:
                        rows.append(("patch %d" % patch, index, value, read,
                                     wanted[which]))
        finally:
            effect.deinit()
        return rows

    def check(self, cls, name):
        self.assertEqual(
            self.anchors_missed(cls), [],
            "%s does not land a bipolar macro on its span's centre or ends "
            "from the MIDI grid; the rows are (path, macro, midi, read, "
            "wanted)" % name)

    def test_every_bipolar_macro_lands_on_its_anchors(self):
        checked = 0
        for name, cls in patch_classes():
            modes = getattr(cls, "MACRO_MODES", None) or {}
            if "BIPOLAR" not in modes.values():
                continue
            with self.subTest(name=name):
                self.check(cls, name)
            checked += 1
        self.assertGreater(checked, 10,
                           "the walk found almost no bipolar classes")

    def test_midi_64_is_what_the_constructor_left_there(self):
        """Where a class's own default for a bipolar macro is the centre of
        its span, the grid must be able to ask for that same number back.
        This is the row that was red: `Fuzz` built at bias 0.000000 and its
        patch 0 asked for +0.007874."""
        centred = 0
        for name, cls in patch_classes():
            modes = getattr(cls, "MACRO_MODES", None) or {}
            for index in sorted(modes):
                if modes[index] != "BIPOLAR":
                    continue
                span = cls._MACRO_RANGES[index]
                centre = (span[0] + span[1]) / 2.0
                effect = cls.create(CountingSource(), 48000)
                try:
                    if effect.macro(index) != centre:
                        continue
                    effect.set_macro(index, 64)
                    with self.subTest(name=name, macro=index):
                        self.assertEqual(
                            effect.macro(index), centre,
                            "%s macro %d is %r at the constructor default "
                            "and MIDI 64 does not reach it"
                            % (name, index, centre))
                    centred += 1
                finally:
                    effect.deinit()
        self.assertGreater(centred, 10,
                           "no class defaults a bipolar macro to its centre, "
                           "so this row proved nothing")

    def test_the_precontract_base_declares_no_bipolar_macro(self):
        """`_core.Effect` still crosses the grid with the plain linear law.
        Nothing on it declares BIPOLAR, which is why the detent lives in
        `_component` alone; a family that needs one is rebuilt first."""
        for name, cls in patch_classes():
            if not issubclass(cls, _core.Effect):
                continue
            modes = getattr(cls, "MACRO_MODES", None) or {}
            with self.subTest(name=name):
                self.assertNotIn(
                    "BIPOLAR", modes.values(),
                    "%s declares a BIPOLAR macro on the pre-contract base, "
                    "which has no centre detent (audiocomponents#87)" % name)

    def test_a_modules_patch_authoring_modes_match_the_class(self):
        """`macro_of` needs each macro's mode, so a module that authors its
        patches from engineering units keeps a `_MODES` tuple beside
        `_MACRO_RANGES`. It must say what `MACRO_MODES` says, or the patch
        table is computed with the wrong law and nothing else notices."""
        checked = 0
        for name, cls in patch_classes():
            module = sys.modules.get(getattr(cls, "__module__", None))
            declared = getattr(module, "_MODES", None)
            if declared is None:
                continue
            modes = getattr(cls, "MACRO_MODES", None) or {}
            with self.subTest(name=name):
                self.assertEqual(
                    tuple(declared),
                    tuple(modes[index] for index in sorted(modes)),
                    "%s's module-level _MODES has drifted from its "
                    "MACRO_MODES" % name)
            checked += 1
        self.assertGreater(checked, 1, "no module authors patches this way")

    def test_planted_fault_the_old_linear_law_is_red(self):
        # The same fixture without the fault is green, so what turns the law
        # red below is the old MIDI law and not the fixture.
        self.assertEqual(self.anchors_missed(CentresOnTheNewLaw), [])
        self.assertEqual(
            self.anchors_missed(CentresOnTheOldLaw),
            [("set_macro", 0, 64, 0.007874015748031482, 0.0),
             ("get_macro", 0, 64, 64.49606299212599, 64),
             ("patch 0", 0, 64, 0.007874015748031482, 0.0)],
            "the old linear law landed on the centre, so the law above "
            "cannot fail")
        with self.assertRaises(AssertionError):
            self.check(CentresOnTheOldLaw, "CentresOnTheOldLaw")


if __name__ == "__main__":
    unittest.main()
