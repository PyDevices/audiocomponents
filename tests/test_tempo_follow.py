"""A synced class follows a host tempo change without a control moving
(audiocomponents#118).

Every class that declares `"tempo_sync"` is held to the same four readings:

- With Sync on, a tempo change followed by `transport_changed()` renders,
  byte for byte, what the same change followed by moving Sync to where it
  already is renders: the class has re-read the tempo as a control move
  would make it. The same change with nothing after it renders something
  else, so the reading can tell the two apart.
- A host that calls `transport_changed()` every block while the tempo holds
  renders the same bytes as one that never calls it.
- With Sync off, `transport_changed()` does not call the transport.
- A class with its Sync switch unwired (`Unwired`, the behaviour before the
  hook) is red on the first reading.

The racks pass the call to their children, and every other component takes
it and does nothing.
"""

import os
import sys
import unittest

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "support"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import audiocore                                            # noqa: E402
import audioeffects                                         # noqa: E402
import kit_probes as probes                                 # noqa: E402

VENDOR = "PyDevices"

RATE = 48000
BLOCK = 256
#: Blocks before the tempo change, and after it.
BEFORE = 8
AFTER = 120


class Host:
    """A transport whose tempo the test moves, counting its reads."""

    def __init__(self, bpm=120.0):
        self.bpm = bpm
        self.reads = 0

    def __call__(self):
        self.reads += 1
        return (True, 0.0, self.bpm, 4, 4)


def material(frames, channels=2, seed=118):
    """Clicks over a quiet noise floor: a delay's repeats and a
    modulator's rate both show in it."""
    rng = np.random.RandomState(seed)
    pcm = np.round(rng.uniform(-1, 1, (frames, channels)) * 600.0)
    pcm[::4800] = 20000
    return pcm.astype(np.int16)


def build(name, host, sync=True):
    frames = (BEFORE + AFTER) * BLOCK
    source = probes.ArraySource(material(frames), rate=RATE)
    effect = audioeffects.create(name, source, RATE, transport=host)
    index = type(effect)._SYNC_MACRO
    effect.set_macro(index, 127 if sync else 0)
    return effect


def render(name, action, bpm_after=90.0, every_block=False):
    """BEFORE blocks at 120 bpm, then the tempo moves to `bpm_after` and
    `action(effect)` runs, then AFTER blocks. With `every_block`, the
    action runs before every pull instead."""
    host = Host(120.0)
    effect = build(name, host)
    out = bytearray()
    for number in range(BEFORE + AFTER):
        if number == BEFORE:
            host.bpm = bpm_after
            if not every_block:
                action(effect)
        if every_block:
            action(effect)
        out += bytes(audiocore.get_buffer(effect.output)[1])
    effect.deinit()
    return bytes(out)


def follow(effect):
    effect.transport_changed()


def touch_sync(effect):
    index = type(effect)._SYNC_MACRO
    effect.set_macro(index, effect.get_macro(index))


def nothing(effect):
    pass


SYNCED = ("DigitalDelay", "TapeDelay", "AnalogDelay", "PingPongDelay",
          "MultiTapDelay", "Phaser", "AutoPan", "Tremolo")


class TheSyncedClasses(unittest.TestCase):

    def test_every_synced_class_is_named_here_and_wired(self):
        found = []
        for name in audioeffects.ALL:
            effect = audioeffects.create(name, probes.ArraySource(
                np.zeros((BLOCK, 2), np.int16), rate=RATE), RATE)
            if "tempo_sync" in effect.capabilities:
                found.append(name)
                self.assertIsNotNone(type(effect)._SYNC_MACRO, name)
                label = type(effect).MACRO_LABELS[type(effect)._SYNC_MACRO]
                self.assertEqual(label, "Sync", name)
            effect.deinit()
        self.assertEqual(sorted(found), sorted(SYNCED))

    def test_a_tempo_change_is_followed_without_a_control_moving(self):
        for name in SYNCED:
            followed = render(name, follow)
            touched = render(name, touch_sync)
            stale = render(name, nothing)
            self.assertEqual(followed, touched, name)
            self.assertNotEqual(followed, stale, name)

    def test_an_unwired_switch_is_red(self):
        # The plant: the class as it was before the hook, whose Sync switch
        # `transport_changed()` does not know, keeps the old tempo.
        for name in SYNCED:
            probe = build(name, Host())
            base, index = type(probe), type(probe)._SYNC_MACRO
            probe.deinit()
            Unwired = type("Unwired", (base,), {"_SYNC_MACRO": None})
            host = Host(120.0)
            frames = (BEFORE + AFTER) * BLOCK
            effect = Unwired(probes.ArraySource(material(frames), rate=RATE),
                             sample_rate=RATE, transport=host)
            effect.set_macro(index, 127)
            out = bytearray()
            for number in range(BEFORE + AFTER):
                if number == BEFORE:
                    host.bpm = 90.0
                    effect.transport_changed()
                out += bytes(audiocore.get_buffer(effect.output)[1])
            effect.deinit()
            self.assertEqual(bytes(out), render(name, nothing), name)
            self.assertNotEqual(bytes(out), render(name, touch_sync), name)

    def test_an_unchanged_tempo_changes_nothing(self):
        for name in SYNCED:
            every = render(name, follow, bpm_after=120.0, every_block=True)
            never = render(name, nothing, bpm_after=120.0)
            self.assertEqual(every, never, name)

    def test_sync_off_reads_no_transport(self):
        for name in SYNCED:
            host = Host(120.0)
            effect = build(name, host, sync=False)
            reads = host.reads
            for _ in range(4):
                host.bpm += 10.0
                effect.transport_changed()
                audiocore.get_buffer(effect.output)
            self.assertEqual(host.reads, reads, name)
            effect.deinit()

    def test_a_steady_tempo_is_read_and_not_reapplied(self):
        # Once a tempo has been followed, the same tempo again is one read
        # of the transport and nothing else.
        for name in SYNCED:
            host = Host(120.0)
            effect = build(name, host)
            effect.transport_changed()
            calls = []
            original = effect._apply_macro
            effect._apply_macro = lambda *a: calls.append(a) or original(*a)
            reads = host.reads
            for _ in range(10):
                effect.transport_changed()
            self.assertEqual(host.reads - reads, 10, name)
            self.assertEqual(calls, [], name)
            effect.deinit()

    def test_a_bad_tempo_is_followed_once(self):
        # A NaN tempo is not equal to itself; it is still one tempo.
        for name in ("DigitalDelay", "Phaser"):
            host = Host(float("nan"))
            effect = build(name, host)
            effect.transport_changed()
            calls = []
            original = effect._apply_macro
            effect._apply_macro = lambda *a: calls.append(a) or original(*a)
            for _ in range(3):
                effect.transport_changed()
            self.assertEqual(calls, [], name)
            effect.deinit()


class EveryOtherComponent(unittest.TestCase):

    def test_an_unsynced_effect_takes_the_call_and_reads_nothing(self):
        for name in audioeffects.ALL:
            if name in SYNCED:
                continue
            host = Host(120.0)
            source = probes.ArraySource(np.zeros((BLOCK, 2), np.int16),
                                        rate=RATE)
            effect = audioeffects.create(name, source, RATE, transport=host)
            reads = host.reads
            host.bpm = 90.0
            effect.transport_changed()
            self.assertEqual(host.reads, reads, name)
            effect.deinit()
            self.assertRaises(RuntimeError, effect.transport_changed)

    def test_a_rack_passes_it_to_its_children(self):
        host = Host(120.0)
        source = probes.ArraySource(material(64 * BLOCK), rate=RATE)
        rack = audioeffects.create(
            "Rack", source, RATE,
            chain=(("DigitalDelay", {"transport": host}),))
        child = rack.effects[0]
        child.set_macro(type(child)._SYNC_MACRO, 127)
        before = child.get_macro(0)
        host.bpm = 60.0
        rack.transport_changed()
        self.assertNotEqual(child.get_macro(0), before)
        rack.deinit()

    def test_an_instrument_takes_the_call(self):
        import audioinstruments
        name = audioinstruments.ALL[0]
        instrument = audioinstruments.create(name, RATE)
        instrument.transport_changed()
        instrument.deinit()


if __name__ == "__main__":
    unittest.main()
