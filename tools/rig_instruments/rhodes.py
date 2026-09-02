"""Playable gestures for `rhodes`, read from the Phase 2 listening guide's
rhodes section (docs/phase2-listening-guide.md).

A gesture module's contract (see generate_rig.py):

    build(measure_peak) -> RigSpec

`measure_peak(velocity)` renders CHORD at `velocity` for a couple of
seconds through the instrument's own current code and returns the peak
sample amplitude (0.0-1.0) - the generator supplies it so the level-match
boost in gesture 2c is computed from whatever the instrument actually does
today, never a hand-typed number that could go stale.

Macro indices, from rhodes.py's own MACRO_LABELS (0-based):
  0 Volume, 1 Tine Level, 2 Body Level, 3 Tremolo Rate, 4 Tremolo Depth,
  5 Overdrive, 6 Tone, 7 Amp Attack, 8 Amp Decay, 9 Amp Sustain,
  10 Amp Release, 11 Key-Off Noise, 12 Master Tune
"""

import math

NAME = "rhodes"

TINE, BODY, TREM_DEPTH = 1, 2, 4

# A "big two-handed chord around C2-C3" (guide, characteristic 2): four
# notes spanning a 5th, low-mid register.
CHORD = (36, 40, 43, 48)          # C2 E2 G2 C3
THUD_CHORD = (36, 40, 43)         # characteristic 4 - held then released
TREMOLO_CHORD = (48, 52, 55)      # C3 E3 G3, mid register per the "Also" test
HELD_NOTE = 60                    # C4 - "one mid-register note" (char. 1, quick ref)
CLICK_NOTE = 41                   # F2 - "one hard staccato low-mid note" (char. 3)

HARD_VEL = 120
SOFT_VEL = 30


def build(measure_peak):
    hard_peak = measure_peak(CHORD, HARD_VEL)
    soft_peak = measure_peak(CHORD, SOFT_VEL)
    boost_db = 20.0 * math.log10(hard_peak / soft_peak) if soft_peak > 0 else 0.0
    boost_gain = 10.0 ** (boost_db / 20.0)

    # The voicing test needs its own level match, for the same reason the bark
    # test does. The guide's criterion is "Tine up / Body down should sound
    # clangy even played gently, the reverse warm even played hard; IF THEY
    # DIFFER ONLY IN LOUDNESS THE BALANCE ISN'T WORKING" - which cannot be
    # answered while the two settings also differ in level. Measured through
    # the instrument's own code at each macro setting, not assumed.
    clangy_peak = measure_peak(CHORD, 40, macros={TINE: 1.0, BODY: 0.0})
    warm_peak = measure_peak(CHORD, HARD_VEL, macros={TINE: 0.0, BODY: 1.0})
    voicing_db = (20.0 * math.log10(warm_peak / clangy_peak)
                  if clangy_peak > 0 else 0.0)
    voicing_gain = 10.0 ** (voicing_db / 20.0)

    notes = []          # (start_s, dur_s, pitch, velocity)
    markers = []         # (start_s, name)
    macro_env = {}       # index -> [(time_s, value_0_1), ...], sorted
    vol_boosts = []      # (start_s, end_s, gain) - applied to the TRACK volume

    def chord(t, dur, pitches, vel):
        for p in pitches:
            notes.append((t, dur, p, vel))

    def macro(index, t, value):
        macro_env.setdefault(index, []).append((t, value))

    # --- 1. The held note fades forever, and sweetens as it fades --------
    # "check this one first": one mid note, mf, held 8-10 s, nothing else
    # sounding. Right: one continuous downward slope, never a plateau; the
    # bell shimmer is gone within a second, leaving a smooth near-flute tail.
    t = 0.0
    markers.append((t, "1. Held note (mf, 9s) -- continuous fade, "
                       "no plateau; bell shimmer -> flute tone within 1s"))
    notes.append((t, 9.0, HELD_NOTE, 90))

    # --- 2. The bark, and the level-matched control -----------------------
    # "check this one first": hard chord, then the identical chord soft.
    # Right: a snarling edge on the hard chord that VANISHES (not just
    # quiets) on the soft one. The guide's own top rule: play it twice,
    # once as struck and once with the soft one turned up to match --
    # if they still sound like the same instrument once level-matched,
    # the trait failed. 2c is that second pass, done for Brad instead of
    # asking him to ride a fader mid-listen.
    t = 12.0
    markers.append((t, "2a. Bark: HARD chord (vel %d) -- snarling edge, "
                       "almost distorted" % HARD_VEL))
    chord(t, 2.0, CHORD, HARD_VEL)

    t = 15.0
    markers.append((t, "2b. Bark: SOFT chord (vel %d), as played -- edge "
                       "should be simply GONE, not quieter" % SOFT_VEL))
    chord(t, 2.0, CHORD, SOFT_VEL)

    t = 18.0
    markers.append((t, "2c. Bark: SOFT chord LEVEL-MATCHED (+%.1f dB fader "
                       "boost to match 2a's peak) -- if this still sounds "
                       "like 2a, the trait failed (guide's own top rule)"
                       % boost_db))
    chord(t, 2.0, CHORD, SOFT_VEL)
    vol_boosts.append((t, t + 2.0, boost_gain))

    # --- 3. A click before the pitch --------------------------------------
    t = 21.5
    markers.append((t, "3. Attack click: hard staccato low-mid note -- "
                       "listen for an unpitched tap before the tone speaks"))
    notes.append((t, 0.12, CLICK_NOTE, 127))

    # --- 4. A soft thud when you let go -----------------------------------
    t = 23.5
    markers.append((t, "4. Key-off thud: soft chord held 2s, released "
                       "normally -- listen right after release for a "
                       "breathy thump"))
    chord(t, 2.0, THUD_CHORD, 50)

    # --- Also: voicing (Tine/Body balance) is a macro, not a note ---------
    # "Tine up / Body down should sound clangy even played gently, the
    # reverse warm even played hard; if they differ only in loudness the
    # balance isn't working." Tine/Body are read at note-on, so the macro
    # step has to land before the chord it shapes, not during it.
    t = 28.0
    macro(TINE, t - 0.1, 1.0)
    macro(BODY, t - 0.1, 0.0)
    markers.append((t, "5a. Voicing CLANGY (Tine max / Body min), played "
                       "GENTLY (vel 40) -- should still sound clangy"))
    chord(t, 2.5, CHORD, 40)

    t = 31.5
    macro(TINE, t - 0.1, 0.0)
    macro(BODY, t - 0.1, 1.0)
    markers.append((t, "5b. Voicing WARM (Tine min / Body max), played "
                       "HARD (vel %d) -- should still sound warm" % HARD_VEL))
    chord(t, 2.5, CHORD, HARD_VEL)
    # 5c: the clangy setting again, level-matched to the warm one, so the
    # question the guide actually asks can be answered. Without this, 5a and
    # 5b differ in loudness as well as voicing and a listener cannot tell
    # which they are hearing.
    t = 35.0
    macro(TINE, t - 0.1, 1.0)
    macro(BODY, t - 0.1, 0.0)
    markers.append((t, "5c. Voicing CLANGY again, LEVEL-MATCHED to 5b "
                       "(%+.1f dB) -- compare against 5b: if they now sound "
                       "like the same voicing, the Tine/Body balance is doing "
                       "nothing but move a fader" % voicing_db))
    chord(t, 2.5, CHORD, 40)
    vol_boosts.append((t, t + 2.5, voicing_gain))

    macro(TINE, t + 2.6, None)     # placeholder resolved below to patch default
    macro(BODY, t + 2.6, None)

    # --- Also: the tremolo, stereo since 1969 ------------------------------
    # The guide's own trait is mono-pulse vs stereo-pan by ERA. rhodes.py's
    # tremolo is one shared LFO with fixed opposite panning approximating
    # the effect - the module has no Stage/Suitcase switch and no true
    # per-channel-phase stereo mode (see the report: this half of the trait
    # cannot be made playable, only Depth on/off can). Depth is read at
    # note-on too, so re-press rather than sweep mid-note.
    t = 36.0
    markers.append((t, "6a. Tremolo Depth = 0 (off) -- rock steady"))
    chord(t, 2.5, TREMOLO_CHORD, 90)

    t = 39.5
    macro(TREM_DEPTH, t - 0.1, 100.0 / 127.0)
    markers.append((t, "6b. Tremolo Depth = high (on) -- even amplitude "
                       "throb. NOTE: this instrument has no Mono/Stereo "
                       "switch (a single shared LFO + fixed panning stands "
                       "in for both), so the guide's side-to-side-vs-"
                       "centre-pulse distinction is NOT playable here -- "
                       "only Depth on/off is."))
    chord(t, 2.5, TREMOLO_CHORD, 90)
    macro(TREM_DEPTH, t + 2.6, 0.0)

    total_seconds = 46.0

    return {
        "notes": notes,
        "markers": markers,
        "macro_env": macro_env,
        "vol_boosts": vol_boosts,
        "total_seconds": total_seconds,
        "chord": CHORD,
    }


#: Traits from the guide's rhodes section this rig does NOT attempt, with
#: why - read by generate_rig.py to fold into its own printed report.
NOT_PLAYABLE = [
    "Suitcase tremolo mono-vs-stereo (era switch): rhodes.py has one shared "
    "ring-mod LFO with fixed opposite panning for both channels and no "
    "Stage/Suitcase mode selector, so there is no second mode to switch to "
    "- only Tremolo Depth on/off is wired (gesture 6).",
]
