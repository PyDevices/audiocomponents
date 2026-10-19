"""A SoundFont 2 bank as an instrument: every melodic preset under one
program change, played through `audiosampler`.

    inst = audioinstruments.create("soundfont", 48000, bank="/sd/FluidR3_GM.sf2")
    inst.program_change(48)        # Strings in bank 0
    inst.note_on(60, 100)

Patch n is Program Change n in the bank's melodic bank (bank 0 for a General
MIDI set), named from the bank; a program the bank lacks is a silent patch
so the numbers stay MIDI's. Bank Select (CC 0 and CC 32) picks another
melodic bank for the next program change, falling back to bank 0 when the
bank has no such preset, as a GM player does. The kit, bank 128, is the
`soundfont_drums` instrument.

The bank is found in this order: the `bank` option to `create()` (a path, or
an open `_sf2.SoundFont`), the `SOUNDFONT` environment variable, then the
first `.sf2` in `~/soundfonts/` (`%USERPROFILE%\\soundfonts` on Windows). The
hydra is read at `create()`; samples are read from the file the first time a
note needs them and kept, so a 148 MB bank costs only the presets you play.
Instruments made from the same path share the open bank and its samples.

The samples kept are bounded: `CACHE_BYTES` of them (8 MB on a board, 64 MB
on a desktop), or what `open_bank(path, cache_bytes=...)` asks for. When a
new one would go over, the samples played least recently are let go first,
and read again from the file if a note wants them later. A voice still
playing a sample keeps it until the voice ends, so a long, dense piece
plays in bounded memory rather than growing it to every sample it touches.

Attenuation. A region's `initialAttenuation` is applied scaled by
`ATTENUATION_SCALE` (0.4): the banks in circulation were voiced on players
that scale it so, and played per the specification's centibels they come out
far quieter and more uneven between presets than their authors heard. The
one constant is the whole convention. Velocity is a square law on top.

Five macros: Volume, Attack and Release (scaling the bank's own envelope,
64 is as written), Tune (bipolar, two semitones each way) and Pan. Pan is
bipolar too: 64 is centre, 0 hard left, 127 hard right. It is an offset
added to each region's own pan, so a stereo pair keeps its spread around
the new centre, clamped at the edges. Moving it re-pans the voices already
sounding, with the engine's ramp, and Control Change 10 on the instrument
drives it, as it does Bank Select; the other GM controllers are the
host's. A program change puts every macro back to the patch's defaults,
Pan at centre.

Thirty-two engine voices, one per region a note resolves to (a stereo pair
is two). A new note with every voice busy steals the oldest releasing voice,
then the oldest. A note in an exclusive class stops the sounding notes of
that class first, which is how the closed hi-hat chokes the open one. Note
off releases a voice through its own release stage; loop mode 3 lets the
sample run on to its end.

Several instruments can share one pool of voices instead, as a General MIDI
module's sixteen parts do: make a `Voices`, pass it as `voices=` to every
`create()`, and play its `output` once. A busy part then takes the voices
an idle one isn't using, a new note anywhere steals the oldest releasing
voice in the whole pool, and there is one sampler to render rather than one
per instrument and a mixer to sum them.

Pure Python over the reader and the engine, so it imports on MicroPython;
`audiosampler` is imported when an instrument is created.
"""

NAME = 'soundfont'
DISPLAY_NAME = 'SoundFont'
CATEGORIES = ('Sampler',)
VERSION = '0.0.1'
VENDOR = "PyDevices"

MACRO_LABELS = ("Volume", "Attack", "Release", "Tune", "Pan")
MACRO_MODES = {
    0: "UNIPOLAR",
    1: "UNIPOLAR",
    2: "UNIPOLAR",
    3: "BIPOLAR",
    4: "BIPOLAR",
}

#: The macro values every patch carries: the bank's own envelope (Attack and
#: Release at 64 scale it by 1.0), no detune, centre pan, volume a little
#: under full.
DEFAULT_MACROS = (100, 64, 64, 64, 64)

#: Patch 0 as a literal for the scanners; a live instrument's `patches` are
#: the bank's presets, built in `create()`.
PATCHES = {
    0: ('Program 0', (100, 64, 64, 64, 64)),
}

#: The Pan macro's index, for hosts that drive it by number.
PAN_MACRO = 4

#: The power `initialAttenuation`'s linear gain is raised to. See the module
#: docstring.
ATTENUATION_SCALE = 0.4

#: Engine voices. A note is one voice per region, so this is 32 mono notes
#: or 16 stereo ones.
MAX_VOICES = 32

#: The percussion bank, by the specification.
PERCUSSION_BANK = 128

#: A voice's state in its slot: the key is down, the key is up and the
#: release is sounding, or faded to silence for the reserve.
HELD, RELEASING, FADED = 0, 1, 2

#: Voices a shared pool has unless told otherwise: what a General MIDI
#: module of the SC-88's generation has, and the engine's ceiling.
SHARED_VOICES = 64

import os
import sys

#: Bytes of samples a bank keeps read from its file: 8 MB on a board, where
#: RAM is counted in tens of megabytes, 64 MB on a desktop.
CACHE_BYTES = (64 if sys.implementation.name == "cpython" else 8) * 1048576

import audioinstruments._sf2 as _sf2
from audioinstruments._support import (
    EVENT_NOTE_ON, EVENT_NOTE_OFF, EVENT_PARAMETER, EVENT_PITCH_BEND,
    EVENT_CONTROL_CHANGE, key_of,
)
from audioinstruments._support import Instrument

#: Semitones of pitch bend at full deflection, either way.
BEND_RANGE = 2.0

_CC_BANK_MSB = 0
_CC_BANK_LSB = 32
_CC_PAN = 10


def _bipolar(value0):
    """A bipolar macro's -1..1 from the 0..1 the event carries: the centre
    detent law of `audioeffects._component.position_of_midi`, so MIDI 64 is
    exactly 0 and 0 and 127 are the ends."""
    midi = value0 * 127.0
    if midi >= 64.0:
        return (midi - 64.0) / 63.0
    return (midi - 64.0) / 64.0


def _panned(region_pan, offset):
    pan = region_pan + offset
    if pan < -1.0:
        return -1.0
    if pan > 1.0:
        return 1.0
    return pan


# --- finding and sharing a bank --------------------------------------------

def _getenv(name):
    getenv = getattr(os, "getenv", None)
    if getenv is None:
        return None
    return getenv(name)


def find_bank(path=None):
    """The `.sf2` to play: `path` when given, else `$SOUNDFONT`, else the
    first `.sf2` in `~/soundfonts/`. Raises OSError naming all three when
    none of them yields a file."""
    if path:
        return path
    env = _getenv("SOUNDFONT")
    if env:
        return env
    home = _getenv("USERPROFILE") or _getenv("HOME") or ""
    folder = home + "/soundfonts"
    try:
        names = sorted(n for n in os.listdir(folder)
                       if n.lower().endswith(".sf2"))
    except OSError:
        names = []
    if names:
        return folder + "/" + names[0]
    raise OSError(
        "no SoundFont found: pass bank=<path> to create(), set the "
        "SOUNDFONT environment variable, or put a .sf2 in %s" % folder)


class _Bank(object):
    """An open bank and the samples read from it, at most `cache_bytes` of
    them, the least recently played let go first.

    `cached` is the bytes kept now; `reads` counts the samples read from
    the file and `evicted` the ones let go, so `reads` above the number of
    distinct samples played is the re-reading a small cache costs.
    """

    def __init__(self, font, cache_bytes=None):
        self.font = font
        self.samples = {}      # shdr index -> array('h') of the whole sample
        self.presets = {}      # (bank, program) -> name
        for bank, program, name in font.presets():
            self.presets[(bank, program)] = name
        self._cache_bytes = CACHE_BYTES if cache_bytes is None else int(cache_bytes)
        self._used = {}        # shdr index -> when it was last played
        self._clock = 0
        self.cached = 0
        self.reads = 0
        self.evicted = 0

    @property
    def cache_bytes(self):
        """The most sample bytes kept. Setting it lets go of samples at once
        when the bank holds more."""
        return self._cache_bytes

    @cache_bytes.setter
    def cache_bytes(self, value):
        self._cache_bytes = int(value)
        self._make_room(0)

    def _make_room(self, size):
        """Let go of the least recently played samples until `size` more
        bytes fit, or nothing is left to let go."""
        samples = self.samples
        used = self._used
        while samples and self.cached + size > self._cache_bytes:
            oldest = None
            when = 0
            for index in samples:
                if oldest is None or used[index] < when:
                    oldest = index
                    when = used[index]
            self.cached -= len(samples.pop(oldest)) * 2
            del used[oldest]
            self.evicted += 1

    def _sample(self, sample):
        """The whole sample as array('h'), from the cache or the file."""
        self._clock += 1
        index = sample.index
        pcm = self.samples.get(index)
        if pcm is None:
            size = (sample.end - sample.start) * 2
            self._make_room(size)
            pcm = self.font.read_sample(sample)
            self.samples[index] = pcm
            self.cached += len(pcm) * 2
            self.reads += 1
        self._used[index] = self._clock
        return pcm

    def has(self, bank, program):
        return (bank, program) in self.presets

    def programs(self, bank):
        """Sorted (program, name) for one bank."""
        out = [(p, n) for (b, p), n in self.presets.items() if b == bank]
        out.sort()
        return out

    def melodic_bank(self):
        """The bank the patch list shows: 0, or the lowest non-percussion
        bank when there is no 0."""
        banks = sorted(set(b for b, _ in self.presets if b != PERCUSSION_BANK))
        if not banks:
            raise ValueError("the SoundFont has no melodic presets")
        return 0 if 0 in banks else banks[0]

    def buffer(self, region):
        """The frames a region plays and its loop points within them."""
        sample = region.sample
        pcm = self._sample(sample)
        length = len(pcm)
        start = region.start - sample.start
        end = region.end - sample.start
        if start < 0:
            start = 0
        if end > length:
            end = length
        if end <= start:
            start, end = 0, length
        if start != 0 or end != length:
            pcm = memoryview(pcm)[start:end]
            length = end - start
        loop_start = region.loop_start - region.start
        loop_end = region.loop_end - region.start
        mode = region.loop_mode
        if mode and not (0 <= loop_start < loop_end <= length):
            # A loop that does not fit the frames is a bank error; play the
            # region through once rather than refuse the note.
            mode = 0
        if mode == 0:
            loop_start, loop_end = 0, length
        return pcm, loop_start, loop_end, mode


_OPEN = {}


def open_bank(bank=None, cache_bytes=None):
    """The shared `_Bank` for `bank` (a path, a `SoundFont`, or None to
    search). Banks opened by path are kept, so two instruments on one file
    read each sample once. `cache_bytes` bounds the samples it keeps
    (`CACHE_BYTES` when None); given for a bank already open, it changes
    that bank's bound."""
    if isinstance(bank, _Bank):
        loaded = bank
    elif hasattr(bank, "regions"):
        loaded = _Bank(bank)
    else:
        path = find_bank(bank)
        loaded = _OPEN.get(path)
        if loaded is None:
            loaded = _Bank(_sf2.SoundFont(path))
            _OPEN[path] = loaded
    if cache_bytes is not None:
        loaded.cache_bytes = cache_bytes
    return loaded


# --- the voices ------------------------------------------------------------

class Voices(object):
    """Engine voices on one sampler, for one instrument or shared by several.

        voices = soundfont.Voices(48000, 2)
        melodic = audioinstruments.create("soundfont", 48000, bank=path,
                                          voices=voices)
        kit = audioinstruments.create("soundfont_drums", 48000, bank=path,
                                      voices=voices)
        audio_out.play(voices.output)

    Every instrument made on it has this sampler as its `output`, so play
    it once. Deinitialising one of them stops its own voices and leaves the
    sampler sounding for the rest; `deinit()` the pool after the last.

    A stolen voice stops at once, and one still sounding clicks. `reserve`
    keeps that many voices ready instead: when fewer are free, the oldest
    releasing voices are faded to silence (the engine ramps a level across
    one block), and a new note takes a faded voice before a sounding one.
    The tails end a little sooner, without the click.

    `gain` scales every voice the pool plays. Sixteen parts summed are far
    louder than one instrument, and the sum is quantised once, so a pool for
    a whole GM module wants headroom: General MIDI players run these banks
    at about 0.2.

    `stolen` counts the voices stopped while still sounding to start a new
    note, `cut` the ones among them that were still held (a note ending
    early), and `faded` the releasing voices faded out for the reserve.
    """

    def __init__(self, sample_rate, channel_count=2,
                 voice_count=SHARED_VOICES, shared=True, reserve=0, gain=1.0):
        self.sampler = _sampler(sample_rate, channel_count, voice_count)
        self.sample_rate = sample_rate
        self.channel_count = channel_count
        self.shared = shared
        #: `slots[i]` is engine voice i: None when free, else `[key, serial,
        #: state, exclusive_class, level, pitch, pan, player]`, where `state`
        #: is `HELD`, `RELEASING` or `FADED`, `level`, `pitch` and `pan` are
        #: the region's own, before the live macros, and `player` is the
        #: instrument's that holds it.
        self.slots = [None] * self.sampler.voice_count
        self.serial = 0
        self.reserve = int(reserve)
        self.gain = float(gain)
        self.stolen = 0
        self.cut = 0
        self.faded = 0

    @property
    def output(self):
        return self.sampler

    @property
    def voice_count(self):
        return len(self.slots)

    def sounding(self):
        """How many voices are sounding now, releases included."""
        voices = self.sampler.voice
        n = 0
        for i in range(len(self.slots)):
            if voices[i].playing:
                n += 1
        return n

    def keep_free(self):
        """Fade the oldest releasing voices until `reserve` are free or
        faded."""
        slots = self.slots
        ready = 0
        for slot in slots:
            if slot is None or slot[2] == FADED:
                ready += 1
        voices = self.sampler.voice
        while ready < self.reserve:
            victim = None
            for i, slot in enumerate(slots):
                if (slot is not None and slot[2] == RELEASING
                        and (victim is None or slot[1] < slots[victim][1])):
                    victim = i
            if victim is None:
                return
            voices[victim].level = 0.0
            slots[victim][2] = FADED
            self.faded += 1
            ready += 1

    def deinit(self):
        self.sampler.deinit()


def _free(slots, i):
    """Free slot `i` and take it out of its player's held notes."""
    slot = slots[i]
    slots[i] = None
    if slot is None:
        return
    held = slot[7].held
    indices = held.get(slot[0])
    if indices is not None:
        if i in indices:
            indices.remove(i)
        if not indices:
            del held[slot[0]]


# --- the player ------------------------------------------------------------

class _Player(object):
    """The voices of one instrument, on its own `Voices` or a shared one.

    `slots` is the pool's: the player's own voices are the slots whose last
    item is the player.
    """

    def __init__(self, bank, voices, default_bank=0):
        self.bank = bank
        self.pool = voices
        self.sampler = voices.sampler
        self.slots = voices.slots
        self.held = {}         # key -> [slot index, ...]
        self.default_bank = default_bank
        self.bank_number = default_bank
        self.program = 0
        self.bank_msb = 0
        self.bank_lsb = 0
        self.volume = DEFAULT_MACROS[0] / 127.0
        self.attack_scale = 1.0
        self.release_scale = 1.0
        self.tune = 1.0
        self.bend = 1.0
        self.pan = 0.0

    # -- preset selection ---------------------------------------------------

    def select(self, bank_number, program):
        """Play `program` from `bank_number`, or from the default bank when
        that bank has no such program; a program no bank has is silent."""
        bank = self.bank
        if (not bank.has(bank_number, program)
                and bank.has(self.default_bank, program)):
            bank_number = self.default_bank
        self.bank_number = bank_number
        self.program = program

    def requested_bank(self):
        """The bank the last Bank Select asked for: the default bank until
        one is sent, then MSB*128+LSB when the file has it, else the MSB
        alone (GS), else the LSB alone (XG)."""
        if self.bank_msb == 0 and self.bank_lsb == 0:
            return self.default_bank
        for candidate in (self.bank_msb * 128 + self.bank_lsb,
                          self.bank_msb, self.bank_lsb):
            if any(b == candidate for b, _ in self.bank.presets):
                return candidate
        return self.bank_msb * 128 + self.bank_lsb

    # -- voices -------------------------------------------------------------

    def _collect(self):
        """Free the slots whose voices have finished, whoever held them."""
        voices = self.sampler.voice
        slots = self.slots
        for i in range(len(slots)):
            if slots[i] is not None and not voices[i].playing:
                _free(slots, i)

    def _free(self, i):
        _free(self.slots, i)

    def _allocate(self):
        slots = self.slots
        for i, slot in enumerate(slots):
            if slot is None:
                return i
        # Every voice busy: the oldest faded one, which is silent, then the
        # oldest releasing one, then the oldest.
        victim = None
        for state in (FADED, RELEASING, HELD):
            for i, slot in enumerate(slots):
                if slot[2] == state and (
                        victim is None or slot[1] < slots[victim][1]):
                    victim = i
            if victim is not None:
                break
        pool = self.pool
        if state != FADED:
            pool.stolen += 1
        if state == HELD:
            pool.cut += 1
        self.sampler.voice[victim].stop()
        _free(slots, victim)
        return victim

    def _choke(self, exclusive_class):
        for i, slot in enumerate(self.slots):
            if (slot is not None and slot[7] is self
                    and slot[3] == exclusive_class):
                self.sampler.voice[i].stop()
                self._free(i)

    def note_on(self, key, pitch, velocity, detune):
        self.release(key)
        self._collect()
        try:
            regions = self.bank.font.regions(self.bank_number, self.program,
                                             pitch, int(velocity * 127 + 0.5))
        except KeyError:
            return
        if not regions:
            return
        pool = self.pool
        pool.serial += 1
        serial = pool.serial
        voices = self.sampler.voice
        detune_ratio = 2.0 ** (detune / 12.0) if detune else 1.0
        # Choke before any of this note's regions start, so a stereo pair
        # in one class does not stop its own other half.
        for region in regions:
            if region.exclusive_class:
                self._choke(region.exclusive_class)
        indices = []
        for region in regions:
            pcm, loop_start, loop_end, mode = self.bank.buffer(region)
            vel = velocity
            if 0 <= region.velocity <= 127:
                vel = region.velocity / 127.0
            level = (region.attenuation ** ATTENUATION_SCALE) * vel * vel
            ratio = region.pitch_ratio * detune_ratio
            i = self._allocate()
            voices[i].play(
                pcm, rate=region.sample_rate,
                pitch=ratio * self.tune * self.bend,
                loop_start=loop_start, loop_end=loop_end, loop_mode=mode,
                level=level * self.volume * pool.gain,
                pan=_panned(region.pan, self.pan),
                delay=region.delay,
                attack=region.attack * self.attack_scale,
                hold=region.hold, decay=region.decay,
                sustain=region.sustain,
                release=region.release * self.release_scale)
            self.slots[i] = [key, serial, HELD, region.exclusive_class,
                             level, ratio, region.pan, self]
            indices.append(i)
        self.held[key] = indices
        if pool.reserve:
            pool.keep_free()

    def release(self, key):
        indices = self.held.pop(key, None)
        if not indices:
            return
        voices = self.sampler.voice
        for i in indices:
            slot = self.slots[i]
            if slot is None or slot[7] is not self:
                continue
            if voices[i].playing:
                voices[i].release()
                slot[2] = RELEASING
            else:
                self.slots[i] = None

    def release_all(self):
        for key in list(self.held):
            self.release(key)

    def sounding(self):
        voices = self.sampler.voice
        n = 0
        for i, slot in enumerate(self.slots):
            if slot is not None and slot[7] is self and voices[i].playing:
                n += 1
        return n

    def stop_all(self):
        for i, slot in enumerate(self.slots):
            if slot is not None and slot[7] is self:
                self.sampler.voice[i].stop()
                self.slots[i] = None
        self.held.clear()

    def relevel(self):
        voices = self.sampler.voice
        for i, slot in enumerate(self.slots):
            if slot is not None and slot[7] is self and slot[2] != FADED:
                voices[i].level = slot[4] * self.volume * self.pool.gain

    def repitch(self):
        voices = self.sampler.voice
        factor = self.tune * self.bend
        for i, slot in enumerate(self.slots):
            if slot is not None and slot[7] is self:
                voices[i].pitch = slot[5] * factor

    def repan(self):
        voices = self.sampler.voice
        offset = self.pan
        for i, slot in enumerate(self.slots):
            if slot is not None and slot[7] is self:
                voices[i].pan = _panned(slot[6], offset)

    # -- events -------------------------------------------------------------

    def handle_event(self, event_type, channel, note_id, data0, value0,
                     value1, sample_position):
        if event_type == EVENT_NOTE_ON and value0 > 0.0:
            self.note_on(key_of(channel, note_id, data0), data0, value0,
                         value1)
        elif event_type in (EVENT_NOTE_OFF, EVENT_NOTE_ON):
            self.release(key_of(channel, note_id, data0))
        elif event_type == EVENT_PARAMETER:
            if data0 == 0:
                self.volume = value0
                self.relevel()
            elif data0 == 1:
                self.attack_scale = 2.0 ** (4.0 * (value0 - 64 / 127.0))
            elif data0 == 2:
                self.release_scale = 2.0 ** (4.0 * (value0 - 64 / 127.0))
            elif data0 == 3:
                self.tune = 2.0 ** ((value0 - 64 / 127.0) * 2.0 / 12.0)
                self.repitch()
            elif data0 == PAN_MACRO:
                self.pan = _bipolar(value0)
                self.repan()
        elif event_type == EVENT_PITCH_BEND:
            self.bend = 2.0 ** (value1 * BEND_RANGE / 12.0)
            self.repitch()
        elif event_type == EVENT_CONTROL_CHANGE:
            if data0 == _CC_BANK_MSB:
                self.bank_msb = int(value0 * 127 + 0.5)
            elif data0 == _CC_BANK_LSB:
                self.bank_lsb = int(value0 * 127 + 0.5)


class SoundFontInstrument(Instrument):
    """An `Instrument` whose program change selects a preset in the bank.

    `programs` maps a patch index to the (bank, program) it selects; the
    melodic instrument's is identity into the melodic bank, the kit's is
    its position in bank 128. Bank Select applies to the melodic one.
    """

    def __init__(self, player, patches, programs, macro_labels, note_map=None,
                 transport=None, bank_select=True):
        self._player = player
        self._programs = programs
        self._bank_select = bank_select
        super().__init__(None, player.handle_event, patches, macro_labels,
                         output=player.sampler, transport=transport,
                         note_map=note_map, schedulable=False)

    @property
    def bank(self):
        """The open bank, for the preset list and `regions()`."""
        return self._player.bank.font

    @property
    def preset(self):
        """(bank, program) playing now."""
        return self._player.bank_number, self._player.program

    @property
    def preset_name(self):
        return self._player.bank.presets.get(self.preset)

    def control_change(self, controller, value, channel=0, sample_position=0):
        """Control Change 10 (Pan) moves the Pan macro, so the macro value
        and the sound agree; the rest reach the player as they are."""
        if controller == _CC_PAN:
            self.set_macro(PAN_MACRO, value, channel=channel,
                           sample_position=sample_position)
            return
        super().control_change(controller, value, channel, sample_position)

    def program_change(self, index, channel=0, note_id=-1, sample_position=0):
        target = self._programs.get(index) if isinstance(index, int) else None
        if target is not None:
            bank_number, program = target
            if self._bank_select:
                bank_number = self._player.requested_bank()
            self._player.select(bank_number, program)
        super().program_change(index, channel, note_id, sample_position)

    def reset(self):
        self._player.stop_all()
        self._player.bank_msb = self._player.bank_lsb = 0
        super().reset()

    @property
    def voices(self):
        """The `Voices` this instrument plays on."""
        return self._player.pool

    def sounding(self):
        """How many of this instrument's own voices are sounding now,
        releases included: on shared `Voices`, the others' are not counted."""
        return self._player.sounding()

    def deinit(self):
        """On a shared `Voices`, stop this instrument's own voices and leave
        the sampler to the others; on its own, release the sampler too."""
        if self._deinited:
            return
        if not self._player.pool.shared:
            super().deinit()
            return
        self.all_notes_off()
        self._player.stop_all()
        self._output = None
        self._deinited = True


def _sampler(sample_rate, channel_count, voice_count=MAX_VOICES):
    import audiosampler
    return audiosampler.Sampler(voice_count=voice_count,
                                channel_count=channel_count,
                                sample_rate=sample_rate)


def voices_for(sample_rate, channel_count, voices=None):
    """`voices` checked against the instrument's format, or a pool of its
    own when None."""
    if voices is None:
        return Voices(sample_rate, channel_count, MAX_VOICES, shared=False)
    if (voices.sample_rate != sample_rate
            or voices.channel_count != channel_count):
        raise ValueError("the shared voices are %d Hz, %d channels"
                         % (voices.sample_rate, voices.channel_count))
    return voices


def create(sample_rate, channel_count=2, transport=None, bank=None,
           voices=None):
    """The bank's melodic presets as one instrument; `bank` is a path, an
    open `SoundFont`, or None to look in the usual places. `voices` is a
    `Voices` to share with other instruments, or None for its own."""
    loaded = open_bank(bank)
    melodic = loaded.melodic_bank()
    programs = loaded.programs(melodic)
    patches = {}
    targets = {}
    top = programs[-1][0]
    names = dict(programs)
    for program in range(top + 1):
        name = names.get(program)
        if name is None:
            name = "Program %d (empty)" % program
        patches[program] = (name, DEFAULT_MACROS)
        targets[program] = (melodic, program)
    player = _Player(loaded, voices_for(sample_rate, channel_count, voices),
                     melodic)
    return SoundFontInstrument(player, patches, targets, MACRO_LABELS,
                               transport=transport)
