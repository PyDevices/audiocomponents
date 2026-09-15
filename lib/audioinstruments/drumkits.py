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
MACRO_MODES = {index: "UNIPOLAR" for index in range(len(MACRO_LABELS))}

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

#: Bytes of PCM the mixer holds. It is the whole reason this instrument has
#: any latency at all: one buffer, 256 stereo frames, 5.3 ms at 48 kHz.
_MIXER_BYTES = 1024

import audiomixer  # noqa: E402

from audioinstruments import load  # noqa: E402
# Not `from audioinstruments import _gm`: MicroPython's import machinery
# asks the package's __getattr__ for that name, which this package defines
# for DRUM_MACHINES/MELODIC, and the submodule never gets imported. The
# dotted form is what every other module here uses for _support.
from audioinstruments._gm import PERCUSSION  # noqa: E402
from audioinstruments._support import (  # noqa: E402
    EVENT_NOTE_ON, EVENT_NOTE_OFF, EVENT_PARAMETER, EVENT_PITCH_BEND,
    EVENT_CONTROL_CHANGE, EVENT_CHANNEL_PRESSURE, EVENT_POLY_PRESSURE,
)
from audioinstruments._support import Instrument  # noqa: E402


def _kit_modules():
    return [load(name) for name in KITS]


def _note_map():
    """Every note any kit answers, under General MIDI's name for it.

    The union, not the intersection: a kit that has no conga is silent on the
    conga notes rather than the notes being missing from the instrument. What
    a sequencer needs from this list is "which keys are worth writing", and
    that is the union.
    """
    notes = set()
    for module in _kit_modules():
        notes.update(note for note, _label in module.NOTE_MAP)
    return tuple((note, PERCUSSION.get(note, "Note %d" % note))
                 for note in sorted(notes))


def _patches():
    """One patch per kit, carrying that kit's own defaults in our slots.

    Selecting a kit is selecting its sound, so the patch restores what a
    fresh one of those machines plays. A slot the kit has no control for
    resolves to the middle of the range: it changes nothing, and a host that
    shows it a value should show a neutral one.
    """
    built = {}
    for index, name in enumerate(KITS):
        module = load(name)
        defaults = module.PATCHES[0][1]
        targets = MACRO_MAP[name]
        built[index] = (
            module.DISPLAY_NAME,
            tuple(64 if target is None else int(defaults[target])
                  for target in targets),
        )
    return built


NOTE_MAP = _note_map()
PATCHES = _patches()


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
