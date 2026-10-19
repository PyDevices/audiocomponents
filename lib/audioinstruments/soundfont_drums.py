"""A SoundFont 2 bank's kits as a drum instrument: bank 128, one patch per
kit, the General MIDI percussion keys 35-81 as the pads.

    kit = audioinstruments.create("soundfont_drums", 48000, bank="/sd/FluidR3_GM.sf2")
    kit.note_on(36)          # Bass Drum 1 on the first kit
    kit.program_change(1)    # the bank's second kit

Patch i is the i-th preset of bank 128 in program order, named from the
bank (a General MIDI set lists its Standard kit first). The bank is found
the way `soundfont` finds it, and the two instruments made from one file
share it. A key the kit has no zone for is silent. The closed hi-hat (42)
and pedal hi-hat (44) stop an open hi-hat (46) that is still ringing when
the bank puts them in one exclusive class, as General MIDI kits do.

The macros are `soundfont`'s: Volume, Attack, Release, Tune and Pan. Pan
(64 centre, 0 left, 127 right) is an offset on each zone's own pan, so a
kit's spread moves as one; it re-pans sounding voices, and Control Change
10 drives it.

`NOTE_MAP` is the whole GM percussion map rather than what any one kit
answers: a bank's kits differ in what they fill, and the map is what a
sequencer writes for.
"""

NAME = 'soundfont_drums'
DISPLAY_NAME = 'SoundFont Drums'
CATEGORIES = ('Drum', 'Sampler')
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

#: Patch 0 as a literal for the scanners; a live kit's `patches` are the
#: bank's, built in `create()`.
PATCHES = {
    0: ('Standard', (100, 64, 64, 64, 64)),
}

#: General MIDI percussion, keys 35-81, under GM's names.
NOTE_MAP = (
    (35, "Acoustic Bass Drum"),
    (36, "Bass Drum 1"),
    (37, "Side Stick"),
    (38, "Acoustic Snare"),
    (39, "Hand Clap"),
    (40, "Electric Snare"),
    (41, "Low Floor Tom"),
    (42, "Closed Hi-Hat"),
    (43, "High Floor Tom"),
    (44, "Pedal Hi-Hat"),
    (45, "Low Tom"),
    (46, "Open Hi-Hat"),
    (47, "Low-Mid Tom"),
    (48, "Hi-Mid Tom"),
    (49, "Crash Cymbal 1"),
    (50, "High Tom"),
    (51, "Ride Cymbal 1"),
    (52, "Chinese Cymbal"),
    (53, "Ride Bell"),
    (54, "Tambourine"),
    (55, "Splash Cymbal"),
    (56, "Cowbell"),
    (57, "Crash Cymbal 2"),
    (58, "Vibraslap"),
    (59, "Ride Cymbal 2"),
    (60, "Hi Bongo"),
    (61, "Low Bongo"),
    (62, "Mute Hi Conga"),
    (63, "Open Hi Conga"),
    (64, "Low Conga"),
    (65, "High Timbale"),
    (66, "Low Timbale"),
    (67, "High Agogo"),
    (68, "Low Agogo"),
    (69, "Cabasa"),
    (70, "Maracas"),
    (71, "Short Whistle"),
    (72, "Long Whistle"),
    (73, "Short Guiro"),
    (74, "Long Guiro"),
    (75, "Claves"),
    (76, "Hi Wood Block"),
    (77, "Low Wood Block"),
    (78, "Mute Cuica"),
    (79, "Open Cuica"),
    (80, "Mute Triangle"),
    (81, "Open Triangle"),
)

import audioinstruments.soundfont as _soundfont


def create(sample_rate, channel_count=2, transport=None, bank=None,
           voices=None):
    """The bank's kits as one instrument; `bank` and `voices` as for
    `soundfont`."""
    loaded = _soundfont.open_bank(bank)
    kits = loaded.programs(_soundfont.PERCUSSION_BANK)
    if not kits:
        raise ValueError("the SoundFont has no percussion bank (128)")
    patches = {}
    targets = {}
    for index, (program, name) in enumerate(kits):
        patches[index] = (name, _soundfont.DEFAULT_MACROS)
        targets[index] = (_soundfont.PERCUSSION_BANK, program)
    player = _soundfont._Player(
        loaded, _soundfont.voices_for(sample_rate, channel_count, voices),
        _soundfont.PERCUSSION_BANK)
    return _soundfont.SoundFontInstrument(
        player, patches, targets, MACRO_LABELS, note_map=NOTE_MAP,
        transport=transport, bank_select=False)
