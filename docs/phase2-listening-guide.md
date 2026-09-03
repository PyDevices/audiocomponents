# Listening guide — the gold pass

`rhodes` · `wurlitzer` · `cs80`  — the three instruments with a hardware
reference that survived scrutiny, and the only ones being rebuilt.

`pianet` · `cp70` · `clavinet` — kept here in full. Their grades fell to
literature (the `pianet` capture is of the later magnetic-pickup Pianet T, the
`cp70` capture is of a CP-**80**), so they are documented and deliberately left
as they are. Read their sections if you ever return to them; do not spend a
listening session on them now.

Written when this was "the five electromechanical pianos". `cs80` joined the
pass from a different family when the gold scrutiny ran, and it is not a piano
at all — its section is the last one in §3 and it needs a different kind of
listening from the rest.

Phase 1 was judged on "is it musical, does it sound good." That caught the
CR-78's missing snare instantly and missed eight kits whose closed hats rang
for the open hat's full decay — because a hat that rings for 400 ms still
sounds like a hat. The fault sounded like music, so there was nothing to
listen *for*.

This is the list of things to listen for. Each one is a **gesture to play**,
then what **right** and **wrong** sound like. Almost every trait is a
difference between two gestures — hard against soft, dry against effected —
so play the pair and judge the pair. Where a claim could not be sourced, the
line says so.

## Before anything else: take loudness out of it

Most tests below are hard against soft, and **anything louder simply sounds
brighter and edgier**. That alone will make a module that does nothing but
move a fader pass the bark test — you play hard, you hear more edge, you pass
it, and the fault has just dressed itself up as the trait. That is the Phase 1
failure wearing a new coat.

So play every hard/soft pair **twice**:

1. Once normally. Note what you hear.
2. Again — but turn the monitor up for the soft one until the two sit at
   about the same loudness in the room, and judge the tone only on this pass.

**If the two sound like the same instrument once they are the same loudness,
the trait failed** — however different they seemed the first time. A real
Rhodes played hard is not just a louder Rhodes; it is a harder, hollower,
more aggressive sound that stays different when you match the levels.

This one habit is worth more than every individual test that follows.

§1 and §2 are the few-minute read — the tells and one gesture per machine.
§3 is what you work from at the keyboard, one instrument at a time; §4
calibrates you on the real thing first. **Leave §5 for last:** it says where
our code might be weak, and reading it early will make you hear faults that
may not be there.

---

## 1. The tells — how these five differ by ear

They all get called "electric piano." Only two of them are even related.

**Does the note die when you let go?**
- **Dies instantly, and no pedal can hold it** → Pianet or Clavinet. Both
  damp with the key itself; neither has, or can have, a sustain pedal.
- **Rings on** → Rhodes, Wurlitzer or CP-70.

**If it dies instantly — does digging in change the tone, or only the level?**
- **A hard metallic snap appears that is simply gone when you play soft** →
  Clavinet. It's a guitar hammer-on: a rubber pad slams a string against an
  anvil and the pickup reads that impact.
- **Hard and soft sound the same, just louder and quieter** → Pianet. It
  plucks — a sticky pad drags a reed until the bond breaks at a roughly fixed
  point, so there's little for your touch to modulate.

**If it rings on — bell, reed, or an actual piano?**
- **A bell, ringing a long time** → Rhodes. Struck tuning-fork tine, magnetic
  pickup. Hold one note against a Wurlitzer note struck equally loud: the
  Rhodes should still be ringing clearly after the Wurlitzer has thinned to
  almost nothing. *Unsourced comparison — the two mechanisms (a struck tine
  with a tonebar resonator against a struck flat reed) make this very likely,
  but no source read this pass states the comparison directly. Calibrate it
  against the reference recordings in §4 before trusting it as a tell.*
- **Reedy and slightly raspy even at ordinary volume, and it *growls* when
  you lean on it** → Wurlitzer. Struck reed swinging inside a charged plate;
  Wikipedia puts its waveform "closer to a sawtooth" against the Rhodes'
  smoother, sine-like output.
- **Unmistakably a piano wired straight to the desk — hammers, steel, a stiff
  clangy bass** → CP-70. It *is* a grand piano with the soundboard left out.

One line each: Rhodes is a bell that fades forever. Wurlitzer barks when you
lean on it and sweetens when you don't. Pianet plucks, ignores your touch,
and stops dead. CP-70 is a real piano with no room around it. Clavinet is a
guitar you play from a keyboard.

---

## 2. Quick reference — one gesture per machine

| Instrument | Play this | Right | Wrong |
|---|---|---|---|
| **rhodes** | One mid note, mf, held 8–10 s, nothing else sounding | Never plateaus — one continuous fade all the way down; and the bell shimmer at the front settles into a smooth near-flute tone within a second | It drops after the attack then holds steady like an organ, or the colour never changes from attack to silence |
| **wurlitzer** | One low-mid chord as hard as you can, then as soft as you can | Two different instruments: a gritty, slightly overdriven growl, then a round vibraphone chime with no edge at all | The same tone at two volumes — the growl with the fader down |
| **pianet** | Same note fortissimo, then pianissimo | Almost identical in character. No new edge when you dig in, nothing rounds off when you back away | Digging in adds a bright edge (Rhodes bark grafted on), or playing soft mellows it (Wurlitzer bite) |
| **cp70** | Big two-handed low-mid chord, pedal down, ringing 5–6 s | Peaks fast and fades, staying focused and direct the whole way. It never blooms | A warm roomy wash that keeps opening up and getting lusher — that's a soundboard, and this machine hasn't got one |
| **clavinet** | One low-mid note as hard as you can, then as soft as you can — listen to the instant it starts | Hard: a biting metallic snap, like a pick dragged hard across a string. Soft: a plain rounded thud with none of the edge | Same brightness both times, only louder |
| **cs80** | Hold a chord, then lean harder into **one** finger only, without re-striking | That note alone moves — brighter and more present — while the others stay exactly where they were | The whole chord swells together (that's channel aftertouch, which every cheap keyboard has), or nothing happens until you re-strike |

---

## 3. Per instrument

### rhodes — Fender Rhodes

Every key drives its own small tuning fork: a felt- or neoprene-tipped hammer
strikes a steel tine, a heavier tonebar beside it stores the strike energy
and keeps the tine ringing, and a magnetic pickup facing the tine's tip reads
it like a guitar pickup reads a string. Nothing feeds the tine once it's
struck, so a Rhodes note can only be decaying — and the pickup reads a
wide-swinging tine differently from a narrow one, which is where the bark
lives.

**1. The held note fades forever, and sweetens as it fades** — *check this
one first*
- **Play:** one mid-register note, solid mf, held 8–10 seconds, nothing else
  sounding.
- **Right:** two things at once. The level is one continuous downward slope,
  no plateau ever, held or not. And the metallic bell shimmer on the front of
  the note is gone a second later, leaving a smooth, almost flute-like tone
  still fading.
- **Wrong:** it drops after the attack then holds steady like an organ until
  release; or the colour is identical from attack to silence, one static
  timbre getting quieter.
- **Why:** the tine is struck once and left alone, and its upper partials die
  faster than the fundamental the tonebar keeps feeding (soundgirls.org).

**2. The bark — and it must *vanish* when you play soft**
- **Play:** a big two-handed chord around C2–C3 as hard as you comfortably
  can, then immediately the same chord as softly as you can while still
  sounding every note.
- **Right:** a snarling edge riding on the hard chord, almost a distorted
  growl, that is *gone* — not merely quieter — on the soft one.
- **Wrong:** the same tone at two volumes. Velocity just moves a fader.
- **Why:** a hard hit swings the tine closer to the pickup than a soft one
  reaches, and the pickup up close isn't linear (chicagoelectricpiano.com).
  *Harder hit, more grit is well sourced; the exact mechanism isn't — the
  academic papers on it wouldn't open.*

**3. A click before the pitch**
- **Play:** one hard staccato low-mid note, everything else silent, and
  listen to the very front of it — the instant your finger lands.
- **Right:** a brief unpitched tap under the tone, like a mallet hitting
  something solid a hair before the note speaks.
- **Wrong:** the tone fading in cleanly out of silence, no percussive
  component at all.
- **Why:** the hammer tip physically striking the tine assembly — harder tips
  give more articulation, felt gives a warmer attack (Vintage Vibe).

**4. A soft thud when you let go**
- **Play:** hold a quiet chord a couple of seconds and release normally, not
  a staccato snap. Listen at the moment of release.
- **Right:** a quiet breathy thump as the keys come up, after the pitch stops.
- **Wrong:** key-up and key-down identical except that the pitch ends.
- **Why:** the felt damper dropping back onto the tine. *Weakly sourced — only
  a sample library documenting that it deliberately captured key-off sounds.*

**Also:** clangy-versus-warm is a **voicing setting**, not something one note
does — on hardware, the resting gap between tine and pickup. Tine up / Body
down should sound clangy even played gently, the reverse warm even played
hard; if they differ only in loudness the balance isn't working. And the
tremolo went **stereo in 1969**: earlier Suitcase amps used a mono
amplitude wobble, and from 1969 the same pattern was translated into
side-to-side panning (fenderrhodes.com). *Corrected: an earlier draft framed
this as Suitcase-pans-versus-Stage-is-mono, which the cited page does not
say — the split is by era, not by cabinet.* **Play:** hold a mid-register
chord with tremolo on, in headphones. **Right:** on the stereo setting the
sound swings side to side across your head while staying about equally loud;
on the mono setting it stays centred and pulses in and out. **Wrong:** the
two settings are indistinguishable, or the stereo one just pulses louder and
softer in both ears at once.

---

### wurlitzer — Wurlitzer 200/200A

A felt hammer strikes a flat steel reed, and the reed sits inside a cutout in
a plate held at high voltage: reed and plate are a capacitor, and their
changing gap *is* the signal. Because that output swings harder as the gap
closes, the same mechanism that makes a note louder makes it dirtier. That
one fact is the whole instrument.

**1. Hard and soft are two different instruments** — *check this one first*
- **Play:** one low-mid chord as hard as you comfortably can, then the
  identical chord as softly as you can.
- **Right:** hard is a gritty, slightly overdriven growl that snaps *into*
  the sound — rougher and edgier, not just bigger. Soft is a rounded,
  vibraphone-like chime with no edge at all.
- **Wrong:** a quiet copy of the same gritty tone, or a hard hit that's only
  a louder and slightly brighter version of the soft one, same grain.
- **Why:** small swings stay in the pickup's gentle zone; a hard strike drives
  the reed into its distorting region. Wikipedia: the loud end is "usually
  described as a bark," the quiet end "sweet and vibraphone-like."

**2. It's reedy even before it barks**
- **Play:** hold a single note or plain octave at ordinary velocity and
  listen *after* the attack, not during it.
- **Right:** a slight rasp or buzz under the pitch — closer to a harmonica
  reed or muted trumpet than a bell.
- **Wrong:** a pure flute-like tone with no grain at any dynamic. That's the
  Rhodes' resting colour, not this machine's.

**3. The pulse is a tremolo, whatever the panel says**
- **Play:** hold one chord with Tremolo Rate and Depth up. Listen only to
  loudness; ignore pitch.
- **Right:** loudness breathing up and down evenly, like a hand on a volume
  knob. The pitch never moves.
- **Wrong:** the pitch itself warbling. That's true vibrato, and the machine
  doesn't do it — the real front panel says "Vibrato" and Wikipedia notes it
  "was incorrectly labelled."

**4. A hard note should sweeten as it rings out** — *reasoned, not documented*
- **Play:** one hard-struck single note, held, left to decay fully.
- **Right:** the growl up front melts into the sweet bell-like tail of
  characteristic 1, purely from the note dying down.
- **Wrong:** the grit keeps exactly the same character and only the volume
  drops.
- **Why:** the same gap-versus-grit mechanism playing out in time as the swing
  shrinks. **No source says this outright** — it follows from the sourced
  mechanism, so treat a failure here as a question, not a verdict.

---

### pianet — Hohner Pianet

A sticky pad on the end of each key clings to a tuned steel reed; pressing
the key drags the reed until the bond breaks and the reed snaps free ringing.
A pluck on the way down, not a strike. On release the same pad lands back on
the reed and kills it. The classic 1960s–70s units read the reed with an
electrostatic pickup, like the Wurlitzer.

**1. The flatline — dynamics barely move it** — *check this one first*
- **Play:** one low-mid note or small chord as hard as you can, then the same
  keys as softly as you can while still getting a clean pluck.
- **Right:** the same sound at two sizes, and nothing more. Level-match them
  and they should be very hard to tell apart at all — no new edge when you
  dig in, nothing rounding off when you back away. This is the one instrument
  where "it barely responds" is the correct answer.
- **Wrong:** digging in adds a bright edge (Rhodes bark grafted on), or
  playing soft mellows and rounds it (Wurlitzer bite).
- **Why:** the note starts when the pad's grip breaks — a fixed threshold, not
  a variable strike. A builder who automated a real Pianet called it "touch
  sensitive to a certain extent" but "one-dimensional... similar to the
  electric guitar" (Logos Foundation); a Hohner history says there "wasn't
  much dynamism available from the keyboard" (clavinet.com). *No source puts
  a number on how much velocity does move, so neither does this guide.*

**2. Dead stop on release — and no pedal, ever**
- **Play:** play a chord, hold a sustain pedal down, lift your fingers off
  the keys.
- **Right:** it dies immediately anyway, exactly as if the pedal weren't
  there. Not a fade — a stop.
- **Wrong:** notes ringing on under the pedal, or even an unpedalled note
  fading over several hundred milliseconds instead of cutting off.
- **Why:** the pad that plucks also damps, so damping is part of the key —
  which, per clavinet.com, "negated the possibility of obtaining sustain via a
  foot pedal."

**3. A pluck-pop, not a thud**
- **Play:** one staccato mid-register note, and listen to how it *starts* —
  the instant your finger lands, before the note has gone anywhere.
- **Right:** a quick metallic sproing — a small spring letting go.
- **Wrong:** a soft rounded thump (that's a hammer instrument), or a smooth
  fade-in with no transient at all.
- **Why:** Rod Argent, who played the most famous Pianet part ever recorded,
  described it as the little metal thing breaking "away from the sticky pad"
  to "go boing" (Mix).

**4. Buzzy at the front, thin and clean by mid-note**
- **Play:** hold one mid-register note 2–3 seconds without retriggering.
- **Right:** a rough, complex onset whose graininess disappears within a
  fraction of a second, leaving a simpler, narrower tone that just fades.
- **Wrong:** equally buzzy the whole way through, or already clean from the
  first millisecond.
- **Why:** Wikipedia describes "a complex mixture of harmonics when the reed
  is first struck, which later reduces to a cleaner sustained tone."

**Also:** it should read bright, nasal and a bit thin — brightest in the
octave or two above middle C, notably less full down low than a Rhodes.
*Unsourced: no source read this pass makes a register-by-register claim about
the real machine. Treat as a hint, not a criterion.* A
mellow, chorus-y wash is the *later* magnetic-pickup Pianet T/M, not the
machine on the records.

---

### cp70 — Yamaha CP-70

A real grand piano — wooden action, felt hammers, steel strings — with the
strings shortened (the lowest under 27 inches, against roughly 7 feet on a
concert grand) and the soundboard simply left out. Piezo pickups on the metal
harp read the strings directly. Real piano attack, no room.

**1. No bloom — it's wired straight to the PA** — *check this one first*
- **Play:** a big two-handed low-mid chord, sustain pedal down, ringing five
  or six seconds, hands off.
- **Right:** present, close, a little hard-edged. Peaks fast and fades,
  staying focused and direct all the way down.
- **Wrong:** a warm roomy wash that keeps opening up and getting lusher,
  shimmer building underneath. That's a soundboard and a room doing work this
  instrument physically cannot do.
- **Why:** the soundboard is omitted by design — weight, and feedback
  rejection on a loud stage (Wikipedia; Yamaha's history page). Unamplified,
  players call it thin and muffled.
- **First:** patch 0 ships with Chorus at 64/127. Pull Chorus to zero before
  judging this.

**2. The clangy, stiff bass**
- **Play:** one low bass note or octave alone, hard, left to ring.
- **Right:** thick and faintly metallic — a stiff clangorous clonk with an
  edge, closer to a slightly out-of-sorts upright than a nine-foot grand.
- **Wrong:** a big warm room-filling low end with a smooth pure fundamental.
- **Why:** short strings tuned to low pitches must be thick and stiff for
  their length. *Sources describe the bass as clunky; "inharmonic" is our own
  physical inference, not an attested CP-70 claim.*

**3. Real hammer attack, real touch**
- **Play:** the same single note as softly as you can, then as hard as you
  can hit it.
- **Right:** level-matched (see the top of this guide), the hard hit is
  **harder in colour, not just in size** — more metallic string in it, a
  brighter and slightly harsher clank on the front of the note, where the
  soft one is rounder and more wooden. Two different tone colours, same
  volume.
- **Wrong:** level-matched, the two are the same sound. If the only way you
  can tell them apart is by turning one down, it is a sample played back at
  different volumes.
- **Why:** a genuine acoustic piano action (Wikipedia; Yamaha). *That a harder
  strike brightens a piano rather than only raising its level is general piano
  acoustics — no source we could read states it for the CP-70 specifically.*

**4. The famous shimmer is bolted on**
- **Play:** a sustained chord with Chorus at maximum, then the same chord
  with Chorus at zero.
- **Right:** up, a swirling seasick doubling like two nearly identical pianos
  a hair out of tune. At zero, plain and direct — genuinely dry.
- **Wrong:** any trace of swirl left at zero. Real CP-70s had no onboard
  chorus; Tony Banks' signature was a CP-70 into a Boss chorus (Wikipedia).

**5. The tremolo is a switch, not a personality**
- **Play:** hold a chord with Tremolo Depth at zero, then bring Depth up at a
  moderate Rate on the same chord.
- **Right:** rock steady at zero; an even volume throb once Depth is up.
- **Wrong:** any pulsing at Depth zero, or a pulse that bends pitch as well
  as volume — the real tremolo is a volume effect only.
- **Why:** the CP-70B panel has its own Tremolo section off the preamp. *We
  could read the manual's section list, not the manual itself — no circuit
  detail is claimed here.*

---

### clavinet — Hohner Clavinet D6

Not a piano at all: an amplified clavichord that behaves like a
keyboard-controlled electric guitar. Each key drives a rubber-tipped pad that
slams a steel string against a fixed anvil — a guitarist's hammer-on — and a
magnetic pickup reads the vibrating segment. Past the anvil every string runs
through a woven yarn damper, so the moment the key lets go the note is killed.
The front panel is a passive mixer and switch bank: no envelope generator, no
moving filter, nothing shaping the note but your hands.

**1. The bark when you dig in** — *check this one first*
- **Play:** one note in the octave below middle C as hard as you can, then
  the same note as softly as you can while still speaking a clear pitch.
  Listen to the attack of each — the instant it starts, not the tail.
- **Right:** the hard hit has a biting snap of high-mid harmonics on top of
  the pitch, gone within a fraction of a second — closer to a pick dragged
  hard across a guitar string than a piano hammer. The soft hit has none of
  it: a plain, rounder thud with the pitch.
- **Wrong:** level-matched, the two differ only in loudness — same
  brightness, same edge.
- **Why:** a harder finger is a harder impact against the anvil, injecting
  more high-frequency energy into the string right where the pickup can read
  it. No circuit does this; it's the strike itself. *Partly unsourced: the
  cited pages (clavinet.com; Wikipedia) confirm the weighted action gives
  per-note dynamic control, i.e. LEVEL. That a harder strike also changes the
  TIMBRE is standard struck-string physics and is what every player describes,
  but no source read this pass states it for the Clavinet specifically. It is
  still the first thing to check — just know the timbral half rests on
  physics, not on a quotation.*

**2. It dies the instant you let go, and nothing can hold it**
- **Play:** hold a chord two full seconds and release. If the patch takes a
  sustain pedal, hold the pedal through the release and check again.
- **Right:** silence, immediately, pedal or no pedal — more like releasing a
  plucked rubber band than a piano key.
- **Wrong:** any ring, bloom or pedal-held tail after key-up. A Rhodes or
  Wurlitzer may ring past release; those have real damper-lift pedals. This
  doesn't.
- **Why:** every string runs permanently through a yarn damper except during
  the instant the anvil holds it (Wikipedia; clavinet.com FAQ).

**3. The funk test — nothing rings, so nothing smears**
- **Play:** a fast, choppy 16th-note vamp on one chord, medium-fast tempo,
  low-mid register.
- **Right:** every note its own discrete percussive event with real silence
  between hits, however fast you go.
- **Wrong:** the pattern blurring into a continuous wash as tempo rises.
- **Why:** this is characteristic 2 heard musically. The style exists
  *because* the machine has no sustain; it isn't a playing choice layered on
  a sustaining instrument.

**4. The switches are four instruments, not a tone knob**
- **Play:** the same low-mid riff on each register in turn — bridge pickup
  alone, centre pickup alone, both in phase, both out of phase.
- **Right:** four distinct sounds. One rounder and bassier, one thinner and
  more nasal, one full and rich, and the out-of-phase pair noticeably thin
  and hollow, as if the pickups were cancelling.
- **Wrong:** a smooth continuous brighter-to-duller sweep between settings.
  That's a tone knob, not a switch matrix.
- **Why:** the pickups sit at different distances from the string's fixed end
  and colour the harmonics differently; the manual describes AB/CD as
  reversing one pickup's polarity "to cancel overtones or to add them"
  (D6 owner's manual; chicagoelectricpiano.com).

**5. Mute on: a dull, dry knock**
- **Play:** the same hard low-mid chord twice, Mute at zero then at maximum.
  Extremes only — the D6 manual says use it fully on or fully off.
- **Right:** muted, even a hard hit collapses at once into a short, dry,
  felt-damped knock — duller and drier, not merely shorter and quieter.
- **Wrong:** a shorter, quieter copy with the same tonal balance.
- **Why:** the mute is a physical slide that, in the manual's own words,
  "puts a damper on the strings and produces a dull, dry sound."

**6. The wah is not the instrument**
- **Play:** the funk vamp again completely dry, Wah Depth at zero.
- **Right:** dry, it should already be a hard, short, plucky sound with real
  bite and a fixed colour — closer to a muted electric guitar than to any
  piano. Everything the wah does is *movement* laid over a sound that was
  already sharp and complete without it.
- **Wrong:** dry, it sounds soft, dull or vague, and only turns into
  something with character once the wah is engaged. If the wah is doing the
  identifying, the instrument underneath is not finished.
- **Why:** its tone controls are static switches. Ernst Zacharias, who designed
  it, distinguished the clean original from "the kind of overdriven auto-wah
  Clavinet beloved of most enthusiasts" (Sound on Sound). The quack is a
  pedal — judge the dry sound as the target.

---

### cs80 — Yamaha CS-80

Not a piano at all, and the odd one out in this guide. Eight true voices, each
built from **two complete synthesizer layers** — sixteen oscillators, and each
layer with its own independent high-pass *and* low-pass resonant filter. Two
things separate it from every other instrument in this library, and neither is
something you stumble into: **polyphonic aftertouch**, which reads how hard you
are leaning on *each individual key* while it sounds, and a **ribbon
controller** — a continuous strip you slide a finger along to bend pitch, with
no frets and no note boundaries. There is also a ring modulator on every voice.

One production run, 1977–79, no mid-life revision — so unlike the Pianet and
the CP-70 there is no "which generation" question to resolve.

**1. Aftertouch is per key, and that is the whole instrument** — *check this
one first*
- **Play:** hold a three- or four-note chord steady. Then, without
  re-striking anything, lean harder into **one** finger only. Then release
  that pressure and lean into a different one.
- **Right:** the note you press into moves — brighter, louder, more present —
  **while the others stay exactly where they were.** You can walk a melody
  through a held chord with pressure alone, never lifting a finger.
- **Wrong:** the whole chord swells together when you lean on any key. That is
  channel aftertouch, which every cheap keyboard has, and it is a different
  instrument. Also wrong: nothing happens at all until you re-strike.
- **Why:** each key has its own pressure sensor, and the voice it owns
  responds alone. This is the single feature a CS-80 is remembered for.

**2. The ribbon slides, it does not step**
- **Play:** hold one note and slide along the ribbon control slowly from one
  end to the other, then quickly.
- **Right:** one unbroken glide, like a finger on a fretless string. No
  stair-stepping, no settling onto semitones, and the speed of the glide is
  exactly the speed of your finger.
- **Wrong:** you hear discrete steps, or it snaps to the nearest semitone, or
  it lags behind and catches up. Any of those is a pitch-bend wheel wearing a
  ribbon's name.

**3. Two layers, not one voice with two settings**
- **Play:** set the two layers to obviously different characters — one dark
  and filtered, one bright and thin — and play a single note. Then bring one
  layer's level to zero and play it again.
- **Right:** with both up you hear **two sounds at once**, each with its own
  filter colour, not a blend that averages them. Muting one leaves the other
  completely intact and unchanged.
- **Wrong:** muting one layer changes the character of the other, or the two
  together sound like a single filter setting somewhere between them.
- **Why:** eight voices of two independent layers — "eight times two patches"
  in the machine's own literature — each with its own filter pair
  (Vintage Synth Explorer).

**4. Both filters, on both layers**
- **Play:** on one layer, sweep the low-pass down until it is dark, then bring
  it back and sweep the high-pass up until it is thin.
- **Right:** both directions work, on **either** layer, and both have audible
  resonance at their corner. You can make a layer thin and hollow (high-pass)
  or dark and heavy (low-pass) independently.
- **Wrong:** one layer only darkens and the other only thins — that is one
  filter type per layer rather than both on each. *This is the specific
  simplification our module is flagged for (§5), so expect it and tell me if
  you hear it.*

**5. Ring modulation should be metallic, not just wobbly**
- **Play:** a single sustained mid note with ring modulation at zero, then
  bring it up slowly.
- **Right:** at low settings a slow tremble; as it comes up the tone turns
  **clangy and inharmonic** — bell-like, slightly out of tune with itself, the
  sound of two frequencies multiplying rather than one being wobbled.
- **Wrong:** it only ever gets more tremolo — amplitude going up and down with
  the pitch unchanged. That is an LFO on the volume, not ring modulation.
- **Why:** the ring modulator is driven by a sub-oscillator whose frequency
  sets the rate and whose voltage sets depth (Yamaha CS-80 instruction manual,
  p.47).

**Also:** it should sound **big** — eight voices of two layers is sixteen
oscillators, and a full chord ought to feel thick and slightly unstable, the
way independently-drifting analogue oscillators do. If a six-note chord sounds
thin or perfectly in tune with itself, something is collapsing layers.

## 4. Reference recordings — calibrate before judging ours

**rhodes** — *Herbie Hancock, "Chameleon"* (Head Hunters, 1973): bark on the
accented low stabs against the softer comping, inside one performance.
*Miles Davis, "Pharaoh's Dance"* (Bitches Brew, 1970), Hancock and Corea both
on Rhodes: decay tails of earlier hits still ringing under newer ones.
*Stevie Wonder, "As"* (1976), Hancock's solo: clean sustained lines, loud
against soft. *Led Zeppelin, "No Quarter"* (1973): the same bell character
outside jazz. Hancock's Mwandishi-era albums for the Suitcase panning tremolo
in headphones — the source names the era, not a track.

**wurlitzer** — *Ray Charles, "What'd I Say"* (1959): the record that made
the instrument, largely dry, stabs at the gritty end. *Queen, "You're My Best
Friend"* (1975): played gently and dry — the sweet end, plus the tremolo
breathing under sustained chords. *Marvin Gaye, "I Heard It Through the
Grapevine"* (1968): percussive stabs and jazzier runs in one track, the best
single A/B. **Don't calibrate on** "The Logical Song" (CE-1 chorus) or
"Money" (wah) — iconic, but the pedals confound everything here.

**pianet** — *The Zombies, "She's Not There"* (1964): the most-cited Pianet
record anywhere, on a classic electrostatic-pickup unit by date; hear the
attack stay identical on every note of the riff, fast runs included. *Genesis,
early 1970s* (Nursery Cryme / Foxtrot / Selling England era): Pianet through
a fuzz box — the fuzz adds grit but the pluck-and-die envelope underneath is
still the Pianet's. *The Beatles, "The Night Before"* and *"I Am the
Walrus"*: how flat the touch response stays across a progression, and how
cleanly each chord cuts off.

**cp70** — *Genesis, "That's All"* (Duke, 1980): highest confidence —
Wikipedia states the main riff is a CP-70 and that Banks' CP-70-into-Boss-
chorus was his signature; hear the real hammer attack driving the shimmer.
His late-70s/80s Genesis catalogue generally for the same texture elsewhere.
**Not "Africa"** — the natural guess and the wrong one; that opening is a
Yamaha CS-80 and a GS-1. Single-blog-sourced, sample before trusting: Billy
Joel "My Life," Peter Gabriel "In Your Eyes," Toto "Hold the Line," Joe
Jackson "Steppin' Out."

**clavinet** — *Stevie Wonder, "Superstition"* (1972): the archetype. Listen
for the snap, and for a tone colour that stays put instead of sweeping.
*Correction: an earlier draft called this "dry, no pedal in the documented
chain." The multitrack breakdown cited in §6 documents roughly eight clavinet
channels — amp mics, separate direct lows and highs, and delay/Echoplex
returns — so it is a heavily produced sound, not a dry one. Use it for the
snap and the fixed colour, not as a dry reference.* *Stevie Wonder, "Higher
Ground"* (1973): same player, same era, through a Mu-Tron III envelope
filter — A/B them to hear exactly what the pedal adds. *Bill Withers, "Use
Me"* (1972): the staccato comping test played properly. *Led Zeppelin,
"Trampled Under Foot"* (1975): dug into hard, outside funk. **Skip
"Chameleon" for clavinet** — its bassline is casually credited to clavinet
and is generally understood to be an ARP synth; we verified neither claim,
which is reason enough not to calibrate on it.

---

## 5. Where we may already be weak

**Read this after you listen.** Nothing here was heard or measured — it is a
reading of the module source only, so it says what the code *could* produce,
never what it sounds like. Every line is a question to check by ear, not a
fault to go hunting for.

**The one that spans all five: velocity mostly moves a fader.** In `rhodes`,
`pianet`, `cp70` and `clavinet`, velocity enters as a single amplitude
multiplier and nothing else — same waveform, same envelope, same filter for a
hard hit and a soft one. `wurlitzer` is the only one letting velocity change
tone, and it does that by opening a lowpass over grit baked in at a fixed
amount, so it uncovers a constant amount of dirt sooner rather than making
more. That is exactly the trap: **louder is not barkier.** If the hard/soft
pairs in §2 come back as "same tone, two volumes," this is likely why.

- **rhodes** — no velocity path to the bark at all. The main envelope also
  has a nonzero sustain level (a held plateau) where characteristic 1 wants
  one continuous fade; whether that's audible depends on the decay rate and
  how long you hold. The key-off thud *is* implemented. The Suitcase tremolo
  is approximated with a shared LFO and fixed opposite panning rather than
  true stereo — the code says so itself — and there's no Stage/Suitcase
  switch.
- **wurlitzer** — the bark melting to sweetness within one note (char. 4)
  isn't attempted: the filter is set once at note-on and held for the whole
  note, so a hard note should stay equally bright until release. The cutoff
  is a fixed frequency rather than tracking pitch, so the sweet end may
  behave differently in the bass than the treble.
- **pianet** — the two most identifying traits are the two most likely to
  fail. Velocity scales amplitude fully and linearly across the whole range,
  the opposite of the flatline; and the default release is around 0.4 s, a
  smooth synth fade where the trait wants a hard stop. The layered
  pluck-then-body design for the buzzy-front trait looks sound on paper. No
  hold-pedal handling exists anywhere in the framework — which happens to
  match the hardware, but it isn't clear yet whether that's a decision or an
  accident.
- **cp70** — dryness comes by omission (there's no reverb stage), and the
  hammer transient and chorus are both modelled directly. Velocity doesn't
  shape tone. The string wavetable is a plain harmonic series with no stretch
  or detune, so nothing in it produces the stiffness behind the clangy bass.
  The voice cap is 12 and each held key costs two or three oscillators, so a
  heavily pedalled dense voicing may drop notes during the very test in §2.
- **clavinet** — no velocity path to brightness. Release is adjustable up to
  about a second, so the module permits a tail the real instrument cannot
  have, and the envelope carries a nonzero sustain level where a struck
  string only decays. Two pickups exist, but as a continuous crossfade
  between two fixed waveforms, never phase-inverted — so the hollow
  out-of-phase register in char. 4 doesn't exist yet. The mute shortens decay
  but doesn't darken the tone.

**Two things that are choices, not defects.** `wurlitzer` exposes "Bite" and
"Bark" macros and `clavinet` exposes "Wah," where the real machines had
neither — touch and an outboard pedal did that work. New macros are allowed;
just judge the dry, macro-neutral sound as the accuracy target. And every
module here caps polyphony at 12–16 voices against instruments fully
polyphonic across 54–88 keys, so a wide pedalled spread can steal notes in a
way no real one would.

---

## 6. Sources

The pages these claims were read from. Nothing was downloaded or
redistributed and no sample library was copied. Full licence calls and dead
ends live in the Phase 2 research notes; this is the short form.

- **rhodes** — Wikipedia "Rhodes piano"; soundgirls.org "The Fender Rhodes";
  chicagoelectricpiano.com "The Fender Rhodes 'Bark'"; fenderrhodes.com
  "Classic Rhodes Effects"; Vintage Vibe hammer-tip and tone-bar-clip
  articles; Red Bull Music Academy Daily (recordings); GroupDIY and Tape Op
  threads, corroborating only. Two academic sources on the pickup
  nonlinearity (ISMA 2014; a UCSB thesis) could not be read.
- **wurlitzer** — Pfeifle, DAFx-17, "Real-Time Physical Model of a Wurlitzer
  and Rhodes Electric Piano" (read in full; licence unstated, mechanism
  restated in our own words, nothing copied); Wikipedia "Wurlitzer electronic
  piano" (CC BY-SA 4.0); Vintage Vibe reed case study; Tropical Fish Vintage;
  Native Instruments blog (recordings only).
- **pianet** — Wikipedia "Hohner Pianet" and "She's Not There" (CC BY-SA
  4.0); clavinet.com Pianet history; Mix, "Classic Tracks: She's Not There"
  (Argent's own words); Logos Foundation's automation write-up; Audiofanzine
  owner reviews. Licences unverified outside Wikipedia; quoted for
  attribution only.
- **cp70** — Wikipedia "Yamaha CP-70," "That's All," "Tony Banks" (CC BY-SA
  4.0); Yamaha's Innovation Road history page; two vintagesynth forum threads
  (muffled unamplified tone, clunky bass, preamp tremolo circuit); the CP-70B
  manual's contents page. The manual and service PDFs would not yield
  readable text.
- **clavinet** — clavinet.com D6 owner's manual and the Clavinet.Com FAQ
  (© Aaron Kipness, read for facts only); Wikipedia "Clavinet" (CC BY-SA
  4.0); chicagoelectricpiano.com tone-controls article; Sound on Sound,
  "Ernst Zacharias & The Hohner Clavinet"; Remaggi et al., DAFx-12, "A Pickup
  Model for the Clavinet" (behaviour described in plain language, nothing
  transcribed); Bobby Owsinski's isolated-clavinets breakdown.
