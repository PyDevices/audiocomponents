"""The drum kits' General MIDI note table, built from the modules themselves.

`lib/audioinstruments/README.md` publishes this table so someone choosing a
kit can see which hits it answers. A table typed by hand is a table that goes
stale, so it is rendered from the live `NOTE_MAP`s here and
`test_metadata_contract.py` holds the README to it.
"""

import audioinstruments

#: The kits, in the order the README lists them, with the column heading each
#: gets. Short headings: twelve columns is already a wide table.
KITS = (
    ("cr78", "CR-78"),
    ("dmx", "DMX"),
    ("drumtraks", "DrumTraks"),
    ("linndrum", "LinnDrum"),
    ("simmons_sdsv", "SDS-V"),
    ("sp1200", "SP-1200"),
    ("tr606", "TR-606"),
    ("tr707", "TR-707"),
    ("tr808", "TR-808"),
    ("tr909", "TR-909"),
)

#: General MIDI's names for the percussion keys these machines use. The list
#: is deliberately only as long as it needs to be: a note appearing here that
#: no kit maps would be a slot we claim and do not fill.
GM_NAMES = {
    35: "Acoustic Bass Drum", 36: "Bass Drum 1", 37: "Side Stick",
    38: "Acoustic Snare", 39: "Hand Clap", 40: "Electric Snare",
    41: "Low Floor Tom", 42: "Closed Hi-Hat", 43: "High Floor Tom",
    44: "Pedal Hi-Hat", 45: "Low Tom", 46: "Open Hi-Hat",
    47: "Low-Mid Tom", 48: "Hi-Mid Tom", 49: "Crash Cymbal 1",
    50: "High Tom", 51: "Ride Cymbal 1", 52: "Chinese Cymbal",
    53: "Ride Bell", 54: "Tambourine", 55: "Splash Cymbal", 56: "Cowbell",
    57: "Crash Cymbal 2", 58: "Vibraslap", 59: "Ride Cymbal 2",
    60: "Hi Bongo", 61: "Low Bongo", 62: "Mute Hi Conga",
    63: "Open Hi Conga", 64: "Low Conga", 69: "Cabasa", 70: "Maracas",
    73: "Short Guiro", 75: "Claves",
}


def maps():
    """`{module: {note: label}}` for every drum machine in the table."""
    return {name: dict(audioinstruments.load(name).NOTE_MAP)
            for name, _heading in KITS}


def render():
    """The markdown table, exactly as the README carries it."""
    live = maps()
    notes = sorted(set().union(*[set(m) for m in live.values()]))
    headings = [heading for _name, heading in KITS]
    lines = ["| Note | General MIDI | " + " | ".join(headings) + " |",
             "|---|---|" + "---|" * len(KITS)]
    for note in notes:
        cells = ["•" if note in live[name] else " "
                 for name, _heading in KITS]
        lines.append("| %d | %s | %s |"
                     % (note, GM_NAMES.get(note, "(no GM slot)"),
                        " | ".join(cells)))
    return "\n".join(lines)
