"""Ten drum machines, one instrument: a program change swaps the kit.

Every machine in this library already answers General MIDI, so one track
plays on any of them. This is the instrument that makes that switchable from
the sequencer: load it once, write the part once, and send a program change
where you want the kit to change. Program 1 is the TR-808, 2 the TR-909, and
so on down `KITS`.

All ten are built at construction and stay resident - 21 ms to build, 87 kB
of heap at rest and 205 kB once every voice of every kit has played, measured
on the MicroPython sidecar - because building a drum machine mid-bar is not
something a sequencer can wait for. Only the kit you are playing is pulled
for audio; the one you just left keeps ringing out until the next change, so
a crash carries over a kit switch the way it would if you hit it and reached
for another box.

A hit a kit has no voice for makes no sound. That is the library's rule and
it is the whole reason this instrument is coherent: a pattern with congas in
it does not turn into noise when you switch to a TR-606, it just loses the
congas until you switch back.

The sixteen macros are one fixed cross-kit set - the host cannot be told new
parameter names on a program change, and a label that lies for nine kits out
of ten is worse than a label that a kit ignores. Each kit maps the ones it
has (`MACRO_MAP`); the rest do nothing on that kit.
"""

NAME = 'drumkits'
DISPLAY_NAME = 'Drum Kits'
CATEGORIES = ('Drum',)
VERSION = '0.0.1'
VENDOR = "PyDevices"

MACRO_LABELS = (
    "Level", "Accent", "Kick Tune", "Kick Decay", "Kick Level", "Snare Tune",
    "Snare Snap", "Snare Level", "Tom Tune", "Tom Decay", "Tom Level",
    "Hat Tone", "CH Decay", "OH Decay", "Cymbal Decay", "Perc Level",
)
MACRO_MODES = {
    0: "UNIPOLAR", 1: "UNIPOLAR", 2: "UNIPOLAR", 3: "UNIPOLAR",
    4: "UNIPOLAR", 5: "UNIPOLAR", 6: "UNIPOLAR", 7: "UNIPOLAR",
    8: "UNIPOLAR", 9: "UNIPOLAR", 10: "UNIPOLAR", 11: "UNIPOLAR",
    12: "UNIPOLAR", 13: "UNIPOLAR", 14: "UNIPOLAR", 15: "UNIPOLAR",
}

#: The kits, in program order. Program 1 in a DAW is index 0.
KITS = (
    "tr808", "tr909", "tr707", "tr606", "cr78",
    "linndrum", "dmx", "drumtraks", "sp1200", "simmons_sdsv",
)

#: `kit -> (target macro index or None, one per MACRO_LABELS slot)`.
#:
#: Written out per kit rather than matched by label text: "Tom Tune" means
#: the middle tom on a three-tom machine and the only tom on a two-tom one,
#: and no string comparison knows that. `None` is a slot that kit has no
#: control for - the macro is still automatable, it just does nothing there,
#: which is the honest answer and the one the panel can show.
MACRO_MAP = {
    # Level Accent KTune KDecay KLevel STune SSnap SLevel TTune TDecay
    # TLevel HatTone CHDecay OHDecay CymDecay PercLevel
    "tr808": (0, 1, 2, 3, None, 5, 6, None, 9, None,
              None, None, 14, 15, 13, None),
    "tr909": (0, 1, 2, 4, None, 5, 7, None, 9, 11,
              None, None, 13, 14, None, 12),
    "tr707": (0, None, None, None, 1, None, None, 2, None, None,
              3, None, None, None, None, 10),
    "tr606": (0, 1, 4, 3, 2, 7, 6, 5, 8, None,
              12, None, 14, 15, 11, None),
    "cr78": (0, 1, 3, 2, None, 5, 4, None, None, None,
             None, 15, None, None, None, 10),
    "linndrum": (0, None, None, None, 1, 3, None, 2, 7, None,
                 6, None, 13, 14, None, 5),
    "dmx": (0, None, 1, 2, None, 3, 4, None, 8, None,
            None, None, 14, 15, None, 10),
    "drumtraks": (0, None, 1, None, 2, 3, None, 4, 5, None,
                  6, 7, None, None, None, 12),
    "sp1200": (0, None, 1, 2, None, 3, 4, None, None, None,
               None, 5, None, None, None, None),
    "simmons_sdsv": (0, None, 2, 4, None, 5, None, None, 9, 12,
                     None, 13, None, None, 15, None),
}

#: Every note any kit answers, under General MIDI's name for it - the union,
#: not the intersection: a kit with no conga is silent on the conga notes
#: rather than the notes being missing from the instrument. What a sequencer
#: needs from this list is "which keys are worth writing", and that is the
#: union. Written out rather than computed because the scanner, the project
#: generators and the catalog all read these declarations as text;
#: `test_cpython_drumkits.py` holds the table to the kits themselves and to
#: `_gm.PERCUSSION`, so it cannot drift from them.
NOTE_MAP = (
    (35, "Acoustic Bass Drum"),
    (36, "Bass Drum 1"),
    (37, "Side Stick"),
    (38, "Acoustic Snare"),
    (39, "Hand Clap"),
    (40, "Electric Snare"),
    (41, "Low Floor Tom"),
    (42, "Closed Hi-Hat"),
    (45, "Low Tom"),
    (46, "Open Hi-Hat"),
    (48, "Hi-Mid Tom"),
    (49, "Crash Cymbal 1"),
    (51, "Ride Cymbal 1"),
    (54, "Tambourine"),
    (55, "Splash Cymbal"),
    (56, "Cowbell"),
    (60, "Hi Bongo"),
    (61, "Low Bongo"),
    (62, "Mute Hi Conga"),
    (63, "Open Hi Conga"),
    (64, "Low Conga"),
    (69, "Cabasa"),
    (70, "Maracas"),
    (73, "Short Guiro"),
    (75, "Claves"),
)

#: One patch per kit, carrying that kit's own defaults in our slots, because
#: selecting a kit is selecting its sound: the patch restores what a fresh one
#: of those machines plays. A slot the kit has no control for sits at 64 - it
#: changes nothing there, and a host showing it a value should show a neutral
#: one. Same reason as NOTE_MAP for writing it out, same test holding it to
#: each machine's own patch 0.
PATCHES = {
    0: ("TR-808", (102, 64, 51, 59, 64, 56, 64, 64, 48, 64,
                   64, 64, 58, 85, 76, 64)),
    1: ("TR-909", (102, 64, 51, 76, 64, 56, 64, 64, 71, 85,
                   64, 64, 100, 64, 64, 64)),
    2: ("TR-707", (102, 64, 64, 64, 102, 64, 64, 102, 64, 64,
                   102, 64, 64, 64, 64, 102)),
    3: ("TR-606", (102, 64, 64, 61, 98, 70, 76, 98, 65, 64,
                   90, 64, 58, 78, 69, 64)),
    4: ("CR-78", (102, 64, 76, 49, 64, 61, 51, 64, 64, 64,
                  64, 78, 64, 64, 64, 102)),
    5: ("LinnDrum", (102, 64, 64, 64, 102, 62, 64, 102, 64, 64,
                     102, 64, 83, 88, 64, 102)),
    6: ("DMX", (102, 64, 64, 67, 64, 56, 76, 64, 97, 64,
                64, 64, 58, 78, 64, 102)),
    7: ("Drumtraks", (102, 64, 64, 64, 102, 64, 64, 102, 64, 64,
                      102, 64, 64, 64, 64, 102)),
    8: ("SP-1200", (102, 64, 64, 64, 64, 64, 64, 64, 64, 64,
                    64, 64, 64, 64, 64, 64)),
    9: ("Simmons SDS-V", (102, 64, 66, 76, 64, 68, 64, 64, 74, 89,
                          64, 67, 64, 64, 87, 64)),
}

#: Bytes of PCM the mixer holds. It is the whole reason this instrument has
#: any latency at all: one buffer, 256 stereo frames, 5.3 ms at 48 kHz.
_MIXER_BYTES = 1024

import audiomixer  # noqa: E402

from audioinstruments import load  # noqa: E402
from audioinstruments._support import (  # noqa: E402
    EVENT_NOTE_ON, EVENT_NOTE_OFF, EVENT_PARAMETER, EVENT_PITCH_BEND,
    EVENT_CONTROL_CHANGE, EVENT_CHANNEL_PRESSURE, EVENT_POLY_PRESSURE,
)
from audioinstruments._support import Instrument  # noqa: E402





class DrumKits(Instrument):
    """The ten kits behind one set of macros and one program list."""

    def __init__(self, sample_rate, channel_count=2, transport=None):
        self._kits = [load(name).create(sample_rate,
                                        channel_count=channel_count,
                                        transport=transport)
                      for name in KITS]
        self._mixer = audiomixer.Mixer(
            voice_count=2, sample_rate=sample_rate,
            channel_count=channel_count, bits_per_sample=16,
            samples_signed=True, buffer_size=_MIXER_BYTES)
        for voice in self._mixer.voice:
            voice.level = 1.0
        # Two voices so a kit change does not cut the tail off the kit you
        # just left: the new one lands on the free voice and the old one
        # rings out where it is. Only those two are ever pulled, so the cost
        # is two kits at a change and one the rest of the time, not ten.
        self._voice = 1
        self._kit_index = None
        super().__init__(
            None, self._dispatch, PATCHES, MACRO_LABELS,
            output=self._mixer, transport=transport, note_map=NOTE_MAP,
            latency_samples=_MIXER_BYTES // (2 * channel_count))

    def _sched_keys(self):
        """The playing kit's, so a scheduled hit lands on the machine the
        dropdown is showing.

        A kit change while a bar is in the queue leaves those hits on the
        outgoing machine - they fire on its synthesizer, which is still being
        pulled on the other mixer voice, which is the same thing that keeps
        its tail from being cut off.
        """
        return self._kits[self._kit_index]._sched_keys()

    @property
    def kit(self):
        """The module name of the kit currently playing."""
        return KITS[self._kit_index]

    def program_change(self, index, channel=0, note_id=-1, sample_position=0):
        """Select a kit, then apply its patch.

        In that order: the macro values the patch carries are this kit's, so
        they have to arrive after the switch or they land on the outgoing
        machine.
        """
        if (isinstance(index, int) and not isinstance(index, bool)
                and 0 <= index < len(KITS) and index != self._kit_index):
            self._select(index)
        super().program_change(index, channel, note_id, sample_position)

    def deinit(self):
        if getattr(self, "_deinited", False):
            return
        super().deinit()
        for kit in self._kits:
            kit.deinit()
        self._kits = []

    def _select(self, index):
        self._voice = 1 - self._voice
        self._kit_index = index
        self._mixer.voice[self._voice].play(self._kits[index].output)

    def _dispatch(self, event_type, channel, note_id, data0, value0, value1,
                  sample_position):
        kit = self._kits[self._kit_index]
        if event_type == EVENT_NOTE_ON:
            kit.note_on(data0, _byte(value0), value1, channel, note_id,
                        sample_position)
        elif event_type == EVENT_NOTE_OFF:
            # To the kit that is playing now, which after a change is not
            # always the one that took the note on. A drum machine releases
            # a voice it does not hold without complaint, and one-shots do
            # not depend on the release, so this stays a non-event.
            kit.note_off(data0, channel, note_id, sample_position)
        elif event_type == EVENT_PARAMETER:
            target = MACRO_MAP[KITS[self._kit_index]][data0]
            if target is not None:
                kit.set_macro(target, value0 * 127.0, channel, note_id,
                              sample_position)
        elif event_type == EVENT_PITCH_BEND:
            kit.pitch_bend(int(value0 * 16383.0 + 0.5), channel,
                           sample_position)
        elif event_type == EVENT_CONTROL_CHANGE:
            kit.control_change(data0, _byte(value0), channel, sample_position)
        elif event_type == EVENT_CHANNEL_PRESSURE:
            kit.channel_pressure(_byte(value0), channel, sample_position)
        elif event_type == EVENT_POLY_PRESSURE:
            kit.poly_pressure(data0, _byte(value0), channel, note_id,
                              sample_position)


def _byte(value):
    """A normalized 0.0-1.0 event value as the MIDI byte a kit expects."""
    if value < 0.0:
        value = 0.0
    elif value > 1.0:
        value = 1.0
    return int(value * 127.0 + 0.5)


def create(sample_rate, channel_count=2, transport=None):
    return DrumKits(sample_rate, channel_count=channel_count,
                    transport=transport)
