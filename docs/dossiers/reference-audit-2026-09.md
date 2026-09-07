# Dossier reference-column audit — 2026-09-07

Documentation-integrity pass for [issue #23](https://github.com/PyDevices/audiocomponents/issues/23).
A reference column populated from the model is invisible — it looks like
agreement. This file scores every figure row the classifier counts, and
records every citation URL this session actually reached.

**Classifier (re-run from repo root):**

```
python3 docs/dossiers/classify_reference_rows.py
```

Last run this session: **25 files, 267 figure rows, 173 license-table rows**
(classifier skips `reference-audit-*.md`).

**What a cloud clone cannot do.** `.reference-captures/` is gitignored.
No pack WAV or stats json was opened. No reference number was computed,
estimated, or "corrected." Rows whose only backing is that tree are
`needs local re-derivation`.

## Commands this session (verbatim)

### Inventory

```
python3 docs/dossiers/classify_reference_rows.py
```

Result (totals line): `TOTAL  173 license / 84 structure / 85 macros / 267 figures / 5 other`.
`FIGURE ROWS TOTAL: 267`. `FILES: 25` (skips `reference-audit-*.md`).

### Mechanical grep (issue comment)

```
rg '/127\*' docs/
```

Result: one match, `docs/dossiers/wurlitzer.md:290`, inside the already-corrected
linear-grid parenthetical (`0.001+2/127*0.5`). Not a live formula.

Neighbor hits of `64/127`, `22/127`, `logmap(47/127` are documented
ratios, not the `/127*` probe.

### Citation URLs

218 unique `http(s)` strings extracted from `docs/dossiers/*.md`
(markdown links, backticks, bare URLs). One of those 218 was a trailing-markdown
artifact (`...vol-1/):**`); the real Monosounds URL is in the same dossier
and was fetched cleanly.

First pass (`urllib` GET, 25 s timeout, 80 KB body, zip/PDF body skipped):
**202 reached (HTTP 200), 16 not reached** (11×403, 4×404, 1 DNS).

Browser-UA retry of the failures plus license pages: cleaned Monosounds
product page HTTP 200; `https://www.electrongate.com/dmxfiles/dmxfiles_faq.html`
HTTP 200; `http://` of the same FAQ HTTP 404. Remaining **not reached**
(see source table below).

Archive.org item metadata was re-fetched as JSON for `licenseurl` /
`rights`. GitHub `license` keys were read from the API. Yeh 2007 was
downloaded (1,055,619 bytes) and text-extracted locally with pypdf
(not committed).

## Counts

| | n |
|---|---|
| Files under `docs/dossiers/` | 25 |
| Figure rows (classifier) | 267 |
| Rows scored `traces` | 137 |
| Rows scored `wording fixed` | 2 |
| Rows scored `needs local re-derivation` | 128 |
| Rows scored `source not reached` | 0 |
| Unique citation URLs extracted | 218 (217 real + 1 artifact) |
| Citation URLs reached this session | 202 first pass; +https electrongate FAQ on retry |
| Citation URLs not reached this session | 15 real (listed below) |

Figure-row `source not reached` is 0 because none of the 267 classifier
rows had a failed URL as its only backing. The 15 dead citations are
license/source lines, marked in those dossiers. Pack-backed numeric rows
are `needs local re-derivation`, not `source not reached`.

`phase1-remainder-evidence.md` and `tr707-evidence.md` contribute **0**
classifier figure rows. Their prose was walked; no extra numeric reference
column was found beyond the instrument dossiers they point at.

## Five tells

1. Same-decimal identity (model measured = reference).
2. Numeric figure with no `n=`, no IQR, and no named source pack.
3. "Exact" / "matched" with no tolerance (not "level-matched" as a method).
4. Wrong-kind source (module default, "today's value", another dossier).
5. Gitignored-only backing (`.reference-captures/` / local zip Readme).

## Sources not reached this session

These URLs were cited and did not yield a usable body. They are **not
evidence**. Dossier license lines that depended on them are marked in the
files.

| URL | This session |
|---|---|
| `http://www.electrongate.com/dmxfiles/dmxfiles_faq.html` | HTTP 404. `https://www.electrongate.com/dmxfiles/dmxfiles_faq.html` is 200. |
| `https://bedroomproducersblog.com/2016/02/19/free-tr-707-samples/` | HTTP 403 |
| `https://digginitsamples.bandcamp.com/album/free-sp1200-drums` | HTTP 403 |
| `https://elektrotanya.com/search.php?text=oberheim+dmx` | HTTP 404 |
| `https://files.elphnt.io/file/ELPHNT/free-downloads/707.zip` | DNS: Name or service not known |
| `https://modwiggler.com/forum/viewtopic.php?t=277962` | HTTP 403 |
| `https://mogigrumbles.bandcamp.com/album/fract-osc-soundtrack` | HTTP 403 |
| `https://oxidesoundlab.bandcamp.com/album/minimoog-model-d-synth-samples-basses-synthwave-80s` | HTTP 403 |
| `https://oxidesoundlab.bandcamp.com/album/tb-303-acid-loops-sample-pack-vol-2-134-bpm-3` | HTTP 403 |
| `https://pixabay.com/sound-effects/minimoog-lead-solo-48367/` | HTTP 403 |
| `https://pubs.aip.org/asa/jasa/article-abstract/148/5/3052/631688` | HTTP 403 (rhodes.md already recorded this) |
| `https://raw.githubusercontent.com/Lytrix/EMU-SP1200/main/LICENSE` | HTTP 404 (sp1200.md already recorded this; GitHub API `license` is null) |
| `https://sourceforge.net/p/open303/code/HEAD/tree/License.txt` | HTTP 403 |
| `https://wave-alchemy.s3.amazonaws.com/downloads/free_samples/wa_free_drum_machine_collection.zip` | HTTP 403 (linndrum.md already recorded this) |
| `https://www.perfectcircuit.com/signal/moog-minimoog-model-d-2022` | HTTP 403 |

## License pages that did resolve, vs the dossier line

A repackager's label is not a license. "Free download" is not a license.
JS shells without the claimed sentence are recorded as reached-but-not-confirming.

| Page | What the fetched body actually states |
|---|---|
| Audiorealism TR-909 pack page | "Free for personal & commercial use under the included license. Attribution appreciated." Included `Readme.txt` not opened (gitignored zip) — that line remains **not reached**. |
| Splice Sample Magic TR-808 pack | JS app. Pack-specific "100% royalty free and cleared for commercial use" **not present** in fetched HTML. Site nav: "100% royalty-free samples" (Splice-wide, not this pack's license page). |
| MusicRadar SampleRadar 808 article | Title still "SampleRadar: 378 free 808 drum samples". Dossier's "royalty-free, no redistribution" sentence **not found** in fetched HTML (page is script-heavy). |
| Samples From Mars terms | Audio products "licensed, not sold"; for compositions/productions only; copying/lending/duplicating/re-selling/trading prohibited. Matches simmons_sdsv.md's EULA quote. |
| Samples From Mars FAQ | "100% royalty free" / license to use in recordings. No "no redistribution" sentence on the FAQ body fetched; the terms page carries the no-copying clause. |
| Pianobook FAQ | "all sample packs uploaded to the Pianobook website should* be copyright free" for commercial and non-commercial compositions; forbidden to sell or redistribute libraries you do not own. Matches rhodes/wurlitzer/cp70. |
| wavparty license | Free use of sounds/loops/instruments except: no redistributing pack files; no using demo tracks in film/video/podcasts/games; no releasing demo tracks as your own music. Matches polysix.md. |
| ELPHNT licensing | "All ELPHNT content is licensed under Creative Commons Zero (CC0)." Matches tr707.md. Live store/707 page no longer hosts the pack (free Ableton landing). |
| Monosounds Minimoog Vol.1 | "100% royalty-free for unlimited commercial use"; "The only thing not allowed is reselling or redistributing the files themselves." Matches minimoog.md. Also still claims "recorded directly from the hardware instrument" — provenance caveat in the dossier stands. |
| Freesound 65762 (Rhodes G1) | "Attribution 4.0" / share and remix with credit. Matches rhodes.md. |
| archive.org `fender_rhodes-sm` | `licenseurl` = `https://creativecommons.org/licenses/by-nc-nd/4.0/`. Matches rhodes.md. CC deed reached. |
| archive.org `e-mu-sample-sets`, `emu-sp-1200-service-manual-1987_202010` | `licenseurl` = Public Domain Mark 1.0. Matches sp1200.md. |
| archive.org Roland/Korg/Moog/Wurlitzer/CR-78/TB-303/TR-606/Linn/DMX/Drumtraks/Pianet T manuals | `licenseurl` null, `rights` null. Matches those dossiers' "license unverified" lines. |
| archive.org `dmx-stock-dmx-sounds` | no licenseurl; description "Custom Fairlight CMI sample pack 48." Matches dmx.md rejection. |
| `elk-audio/mda-vst2` LICENSE | MIT. Matches rhodes.md. |
| `elk-audio/mda-vst3` COPYING | GNU GPL v3. Matches rhodes.md. |
| `sonicarchetype/TR909` LICENSE | MIT, Copyright (c) 2025 SONIC ARCHETYPE. Matches tr909.md. |
| `hal0zer0/openwurli` LICENSE | GNU GPL v3. Matches wurlitzer.md. |
| `vincentriemer/io-808` | GitHub API `license.key=mit`. Matches tr808.md's MIT call. |
| `attilammagyar/js80p` | GitHub API `license.key=gpl-3.0`. Matches cs80.md. |
| `zynthian/moog` | GitHub API `license.key=mit`. Matches minimoog.md. |
| `thecowgoesmoo/TwinCl` | GitHub API `license.key=mit`. Matches clavinet.md. |
| `Lytrix/EMU-SP1200` | GitHub API `license=null`; LICENSE file 404. Matches sp1200.md. |
| Iowa MIS.html | "freely available on this website and may be downloaded and used for any projects, without restrictions." Matches karplus.md. |
| Electric Druid SSM2044 page | "CC BY-NC-SA 4.0" in the footer. Matches polysix.md. |
| clavinet.com/terms.php | Site-wide copyright; reproduction strictly prohibited. Matches clavinet.md. |
| WeTransfer `we.tl/AjC4FCLeMv` | "We couldn't load some important parts of our website." Matches minimoog.md's dead Legowelt download. |
| Legowelt samples page | Reached; no commercial license sentence found (dossier already records donation-only). |
| Wikipedia TR-808 / 909 / 707 / LinnDrum / DMX | Reached; infobox polyphony 12 / 11 voices / 10 notes / 12 voices / 8-voice still present. |

## Document-only edits made this pass

- Table-level `reference figure unverified: needs re-derivation from <pack>` markers on pack-backed criteria tables.
- tr808.md §5c rimshot τ: same-decimal identity marker (27.1 / 27.1). Number not changed.
- linndrum.md Bass Drum note: "exactly" removed as a match claim.
- License / dead-link wording where the fetch disagreed or failed (Splice, MusicRadar, http electrongate, 403/404 citations).
- No figure was recomputed.

## Findings table

One row per classifier figure row. Verdicts: `traces` / `wording fixed` / `needs local re-derivation` / `source not reached`.

| dossier | row | verdict | evidence |
|---|---|---|---|
| `clavinet.md` | L269#1 1. Attack transient differs in brightness, hard vs. soft velocity, level-matched | traces | Qualitative DAFx-12 / D6-manual criterion; PDF https://www.dafx.de/paper-archive/2012/papers/dafx12_submission_62.pdf reached (HTTP 200, binary PDF). No pack median in this row. |
| `clavinet.md` | L269#2 2. Pickup-mix extremes are two distinct timbres, not one filtered continuum | traces | Qualitative DAFx-12 / D6-manual criterion; PDF https://www.dafx.de/paper-archive/2012/papers/dafx12_submission_62.pdf reached (HTTP 200, binary PDF). No pack median in this row. |
| `clavinet.md` | L269#3 3. An anti-phase pickup sum is thinner/hollower than an in-phase sum | traces | Qualitative DAFx-12 / D6-manual criterion; PDF https://www.dafx.de/paper-archive/2012/papers/dafx12_submission_62.pdf reached (HTTP 200, binary PDF). No pack median in this row. |
| `clavinet.md` | L269#4 4. Brilliance macro sweeps a real spectral rolloff | traces | Brilliance sweep is a module-range self-check (tell 4), already sourced to clavinet.py, not a pack figure. |
| `clavinet.md` | L269#5 5. Wah produces a periodic, audible cutoff sweep during a held note | traces | Wah rate 0.5–10.5 Hz is a module-range self-check (tell 4), not a pack figure. |
| `clavinet.md` | L269#6 6. Mute shortens decay/sustain but — per the manual's own "dull" wording — should a | traces | Qualitative DAFx-12 / D6-manual criterion; PDF https://www.dafx.de/paper-archive/2012/papers/dafx12_submission_62.pdf reached (HTTP 200, binary PDF). No pack median in this row. |
| `clavinet.md` | L269#7 7. A struck string's decay is a continuous fade, not a hold at a fixed nonzero plat | traces | Qualitative DAFx-12 / D6-manual criterion; PDF https://www.dafx.de/paper-archive/2012/papers/dafx12_submission_62.pdf reached (HTTP 200, binary PDF). No pack median in this row. |
| `clavinet.md` | L281#1 8. Note dies immediately on key-up, pedal or no pedal | traces | Qualitative D6-manual / guide criterion, blocked on note-off. No pack median. |
| `clavinet.md` | L281#2 9. Release is nearly instantaneous, not a fade | traces | Qualitative D6-manual / guide criterion, blocked on note-off. No pack median. |
| `clavinet.md` | L281#3 10. Fast repeated notes stay discrete ("nothing rings, so nothing smears") | traces | Qualitative D6-manual / guide criterion, blocked on note-off. No pack median. |
| `cp70.md` | L278#1 Attack: unpitched hammer-click energy present before/under pitch onset | traces | Qualitative proposed criterion; no numeric pack/hardware figure in the target column. |
| `cp70.md` | L278#2 Attack brightness scales with velocity (currently does not — §5) | traces | Qualitative proposed criterion; no numeric pack/hardware figure in the target column. |
| `cp70.md` | L278#3 Steady-tone spectral envelope (harmonic roll-off) at a few Brilliance settings | traces | Qualitative proposed criterion; no numeric pack/hardware figure in the target column. |
| `cp70.md` | L278#4 Decay time constant (tau) at default and extreme Decay macro settings | traces | Qualitative proposed criterion; no numeric pack/hardware figure in the target column. |
| `cp70.md` | L278#5 No-bloom: spectral centroid / energy does not grow after onset (no swelling reverberant bo | traces | Qualitative proposed criterion; no numeric pack/hardware figure in the target column. |
| `cp70.md` | L278#6 Double-string unison detune amount above the stringing break, if adopted (§5) | traces | Qualitative proposed criterion; no numeric pack/hardware figure in the target column. |
| `cp70.md` | L278#7 Chorus-off dryness (pedal effect fully absent at Chorus=0) | traces | Qualitative proposed criterion; no numeric pack/hardware figure in the target column. |
| `cp70.md` | L278#8 Tremolo rate/depth accuracy vs panel range | traces | Qualitative proposed criterion; no numeric pack/hardware figure in the target column. |
| `cp70.md` | L278#9 Master tuning / stretch (no Railsback-style stretch modeled — `WAVE_STRING`'s harmonic ser | traces | Qualitative proposed criterion; no numeric pack/hardware figure in the target column. |
| `cp70.md` | L278#10 Key-release / damping behavior | traces | Qualitative proposed criterion; no numeric pack/hardware figure in the target column. |
| `cr78.md` | L38#1 CHCR78.wav | needs local re-derivation | n=1 SFM CR-78 file stats; only backing is gitignored `.reference-captures/cr78/`. Needs re-derivation from the Samples From Mars CR-78 pack. |
| `cr78.md` | L38#2 OHCR78.wav | needs local re-derivation | n=1 SFM CR-78 file stats; only backing is gitignored `.reference-captures/cr78/`. Needs re-derivation from the Samples From Mars CR-78 pack. |
| `cr78.md` | L270#1 Claves | traces | Module overlap experiment (Claves/Cowbell merge), not a hardware reference column. |
| `cr78.md` | L270#2 Cowbell | traces | Module overlap experiment (Claves/Cowbell merge), not a hardware reference column. |
| `cr78.md` | L383#1 Closed Hat | needs local re-derivation | Hat tau/centroid copied from the n=1 SFM files in the L36 table. Needs re-derivation from the Samples From Mars CR-78 pack. |
| `cr78.md` | L383#2 Open Hat | needs local re-derivation | Hat tau/centroid copied from the n=1 SFM files in the L36 table. Needs re-derivation from the Samples From Mars CR-78 pack. |
| `cr78.md` | L401#1 BD | traces | Header already names these as today's cr78.py values with literature support, not pack medians. Tell 4, already labeled. |
| `cr78.md` | L401#2 SD | traces | Header already names these as today's cr78.py values with literature support, not pack medians. Tell 4, already labeled. |
| `cr78.md` | L401#3 RS | traces | Header already names these as today's cr78.py values with literature support, not pack medians. Tell 4, already labeled. |
| `cr78.md` | L401#4 Hat/Cymbal | traces | Header already names these as today's cr78.py values with literature support, not pack medians. Tell 4, already labeled. |
| `cr78.md` | L401#5 Bongo Hi/Lo | traces | Header already names these as today's cr78.py values with literature support, not pack medians. Tell 4, already labeled. |
| `cr78.md` | L401#6 Claves | traces | Header already names these as today's cr78.py values with literature support, not pack medians. Tell 4, already labeled. |
| `cr78.md` | L401#7 Cowbell | traces | Header already names these as today's cr78.py values with literature support, not pack medians. Tell 4, already labeled. |
| `cr78.md` | L401#8 Guiro | traces | Header already names these as today's cr78.py values with literature support, not pack medians. Tell 4, already labeled. |
| `cr78.md` | L401#9 Tambourine | traces | Header already names these as today's cr78.py values with literature support, not pack medians. Tell 4, already labeled. |
| `cr78.md` | L401#10 Maracas | traces | Header already names these as today's cr78.py values with literature support, not pack medians. Tell 4, already labeled. |
| `cr78.md` | L401#11 Metal Beat | traces | Header already names these as today's cr78.py values with literature support, not pack medians. Tell 4, already labeled. |
| `cr78.md` | L422#1 SD | traces | Already labeled derived-not-measured / house cross-kit norm. Tell 4, already labeled. No CR-78 snare pack to re-derive from. |
| `cr78.md` | L422#2 every other voice | traces | Already labeled derived-not-measured / house cross-kit norm. Tell 4, already labeled. No CR-78 snare pack to re-derive from. |
| `cr78.md` | L511#1 Snare LUFS | traces | Peer-kit field and sibling drumtraks, not a CR-78 hardware reference column. Tell 4 (wrong-kind source) already explicit in the header. |
| `cr78.md` | L511#2 Snare peak | traces | Peer-kit field and sibling drumtraks, not a CR-78 hardware reference column. Tell 4 (wrong-kind source) already explicit in the header. |
| `cr78.md` | L511#3 tau | traces | Peer-kit field and sibling drumtraks, not a CR-78 hardware reference column. Tell 4 (wrong-kind source) already explicit in the header. |
| `cr78.md` | L511#4 centroid | traces | Peer-kit field and sibling drumtraks, not a CR-78 hardware reference column. Tell 4 (wrong-kind source) already explicit in the header. |
| `cr78.md` | L511#5 `f_early` / `f_late` | traces | Peer-kit field and sibling drumtraks, not a CR-78 hardware reference column. Tell 4 (wrong-kind source) already explicit in the header. |
| `cr78.md` | L511#6 energy < 500 Hz | traces | Peer-kit field and sibling drumtraks, not a CR-78 hardware reference column. Tell 4 (wrong-kind source) already explicit in the header. |
| `cr78.md` | L511#7 energy > 2 kHz | traces | Peer-kit field and sibling drumtraks, not a CR-78 hardware reference column. Tell 4 (wrong-kind source) already explicit in the header. |
| `cs80.md` | L180#1 1. 8-voice polyphony ceiling holds, 9th note steals | traces | Qualitative / literature proposed criterion; no pack median. mogigrumbles Bandcamp identity page HTTP 403 this session (not used as the numeric source here). |
| `cs80.md` | L180#2 2. Two-layer detune/timbre-blend character audible under `Layer II Mix` | traces | Already states the 0.5% detune is the module's own prior choice, unverified. Tell 4, already labeled. No pack figure. |
| `cs80.md` | L180#3 3. Ring modulator depth tracks an AC-voltage-style control, rate tracks a sub-oscil | traces | Qualitative / literature proposed criterion; no pack median. mogigrumbles Bandcamp identity page HTTP 403 this session (not used as the numeric source here). |
| `cs80.md` | L180#4 4. Poly aftertouch modulates amplitude (and, on real hardware, reportedly vibrato/f | traces | Wikipedia CS-80 page reached; dossier already flags the poly-AT vibrato/filter claim as search-summary, not a page quote. |
| `cs80.md` | L180#5 5. Filter topology: HP+LP in series per layer, not split across layers | traces | Qualitative / literature proposed criterion; no pack median. mogigrumbles Bandcamp identity page HTTP 403 this session (not used as the numeric source here). |
| `dmx.md` | L350#1 Frequency response ceiling | traces | Literature-derived, nothing measured — table already says so. Manual metadata reached; Wikipedia polyphony-8 reached. |
| `dmx.md` | L350#2 Dynamic range | traces | Literature-derived, nothing measured — table already says so. Manual metadata reached; Wikipedia polyphony-8 reached. |
| `dmx.md` | L350#3 Companding character | traces | Literature-derived, nothing measured — table already says so. Manual metadata reached; Wikipedia polyphony-8 reached. |
| `dmx.md` | L350#4 DAC smoothing | traces | Literature-derived, nothing measured — table already says so. Manual metadata reached; Wikipedia polyphony-8 reached. |
| `dmx.md` | L350#5 Hi-Hat decay shape | traces | Literature-derived, nothing measured — table already says so. Manual metadata reached; Wikipedia polyphony-8 reached. |
| `dmx.md` | L350#6 Per-card monophony | traces | Literature-derived, nothing measured — table already says so. Manual metadata reached; Wikipedia polyphony-8 reached. |
| `dmx.md` | L350#7 Voice ceiling | traces | Literature-derived, nothing measured — table already says so. Manual metadata reached; Wikipedia polyphony-8 reached. |
| `dmx.md` | L350#8 Card typology | traces | Literature-derived, nothing measured — table already says so. Manual metadata reached; Wikipedia polyphony-8 reached. |
| `drumtraks.md` | L341#1 Duration | needs local re-derivation | n=1 ClapDtrax15.wav stats from SFM free drums. Gitignored json. Needs re-derivation from that pack. |
| `drumtraks.md` | L341#2 Peak | needs local re-derivation | n=1 ClapDtrax15.wav stats from SFM free drums. Gitignored json. Needs re-derivation from that pack. |
| `drumtraks.md` | L341#3 tau (1/e decay) | needs local re-derivation | n=1 ClapDtrax15.wav stats from SFM free drums. Gitignored json. Needs re-derivation from that pack. |
| `drumtraks.md` | L341#4 T60 (extrapolated) | needs local re-derivation | n=1 ClapDtrax15.wav stats from SFM free drums. Gitignored json. Needs re-derivation from that pack. |
| `drumtraks.md` | L341#5 f_early (0-50ms post-peak) | needs local re-derivation | n=1 ClapDtrax15.wav stats from SFM free drums. Gitignored json. Needs re-derivation from that pack. |
| `drumtraks.md` | L341#6 f_late (100-300ms post-peak) | needs local re-derivation | n=1 ClapDtrax15.wav stats from SFM free drums. Gitignored json. Needs re-derivation from that pack. |
| `drumtraks.md` | L341#7 Spectral centroid | needs local re-derivation | n=1 ClapDtrax15.wav stats from SFM free drums. Gitignored json. Needs re-derivation from that pack. |
| `drumtraks.md` | L362#1 Voice/channel count | traces | Literature/structural criterion (vintagesynth/muzines/Wikipedia). Angelspit 7.8 kHz row is flagged-not-confirmed in the dossier itself. |
| `drumtraks.md` | L362#2 Tune/level range | traces | Literature/structural criterion (vintagesynth/muzines/Wikipedia). Angelspit 7.8 kHz row is flagged-not-confirmed in the dossier itself. |
| `drumtraks.md` | L362#3 Bandwidth ceiling | traces | ≈7.8 kHz bandwidth is flagged-not-confirmed from Angelspit. Page reached this session; dossier already refuses to treat it as confirmed. |
| `drumtraks.md` | L362#4 Hi-Hat choke | traces | Literature/structural criterion (vintagesynth/muzines/Wikipedia). Angelspit 7.8 kHz row is flagged-not-confirmed in the dossier itself. |
| `drumtraks.md` | L362#5 Tom count | traces | Literature/structural criterion (vintagesynth/muzines/Wikipedia). Angelspit 7.8 kHz row is flagged-not-confirmed in the dossier itself. |
| `karplus.md` | L214#1 1. Loop filter is a one-zero average of adjacent samples, feedback gain < 1 sets de | traces | Algorithm-match criterion. CCRMA KS chapter reached (one-zero filter text present). UIowa MIS grant reached on MIS.html. |
| `karplus.md` | L214#2 2. Pick-position comb filter subtracts a delayed copy of the excitation from itself | traces | Algorithm-match criterion. CCRMA KS chapter reached (one-zero filter text present). UIowa MIS grant reached on MIS.html. |
| `karplus.md` | L214#3 3. Pitch is set by delay-line length in samples, `≈ sample_rate / f0` | traces | Algorithm-match criterion. CCRMA KS chapter reached (one-zero filter text present). UIowa MIS grant reached on MIS.html. |
| `karplus.md` | L214#4 4. Excitation is a full-spectrum noise burst, optionally shaped for dynamic level | traces | Algorithm-match criterion. CCRMA KS chapter reached (one-zero filter text present). UIowa MIS grant reached on MIS.html. |
| `karplus.md` | L214#5 5. General plausibility: rendered output should sound like *a* plucked string, not  | traces | Algorithm-match criterion. CCRMA KS chapter reached (one-zero filter text present). UIowa MIS grant reached on MIS.html. |
| `linndrum.md` | L320#1 Bass Drum | needs local re-derivation | Pack τ/f_early from hyperreal (n=2), gitignored. Note claimed the 65 Hz fundamental 'matches the module's existing default bd_pitch = 65.0 exactly' (tells 3+4). Wording changed this pass so 'exact' cannot be read as a pass. Number not recomputed. |
| `linndrum.md` | L320#2 Snare | needs local re-derivation | Hyperreal capture stats; gitignored `.reference-captures/linndrum/hyperreal/`. Needs re-derivation from that pack. |
| `linndrum.md` | L320#3 Rimshot | needs local re-derivation | Hyperreal capture stats; gitignored `.reference-captures/linndrum/hyperreal/`. Needs re-derivation from that pack. |
| `linndrum.md` | L320#4 Clap | needs local re-derivation | Hyperreal capture stats; gitignored `.reference-captures/linndrum/hyperreal/`. Needs re-derivation from that pack. |
| `linndrum.md` | L320#5 Low Tom | needs local re-derivation | Hyperreal capture stats; gitignored `.reference-captures/linndrum/hyperreal/`. Needs re-derivation from that pack. |
| `linndrum.md` | L320#6 Mid Tom | needs local re-derivation | Hyperreal capture stats; gitignored `.reference-captures/linndrum/hyperreal/`. Needs re-derivation from that pack. |
| `linndrum.md` | L320#7 Hi Tom | needs local re-derivation | Hyperreal capture stats; gitignored `.reference-captures/linndrum/hyperreal/`. Needs re-derivation from that pack. |
| `linndrum.md` | L320#8 Conga Hi | needs local re-derivation | Hyperreal capture stats; gitignored `.reference-captures/linndrum/hyperreal/`. Needs re-derivation from that pack. |
| `linndrum.md` | L320#9 Conga Mid | needs local re-derivation | Hyperreal capture stats; gitignored `.reference-captures/linndrum/hyperreal/`. Needs re-derivation from that pack. |
| `linndrum.md` | L320#10 Conga Lo | needs local re-derivation | Hyperreal capture stats; gitignored `.reference-captures/linndrum/hyperreal/`. Needs re-derivation from that pack. |
| `linndrum.md` | L320#11 Cabasa | needs local re-derivation | Hyperreal capture stats; gitignored `.reference-captures/linndrum/hyperreal/`. Needs re-derivation from that pack. |
| `linndrum.md` | L320#12 Tambourine | needs local re-derivation | Hyperreal capture stats; gitignored `.reference-captures/linndrum/hyperreal/`. Needs re-derivation from that pack. |
| `linndrum.md` | L320#13 Cowbell | needs local re-derivation | Hyperreal capture stats; gitignored `.reference-captures/linndrum/hyperreal/`. Needs re-derivation from that pack. |
| `linndrum.md` | L320#14 Closed Hat | needs local re-derivation | Hyperreal capture stats; gitignored `.reference-captures/linndrum/hyperreal/`. Needs re-derivation from that pack. |
| `linndrum.md` | L320#15 Open Hat | needs local re-derivation | Hyperreal capture stats; gitignored `.reference-captures/linndrum/hyperreal/`. Needs re-derivation from that pack. |
| `linndrum.md` | L320#16 Crash | needs local re-derivation | Hyperreal capture stats; gitignored `.reference-captures/linndrum/hyperreal/`. Needs re-derivation from that pack. |
| `linndrum.md` | L320#17 Ride | needs local re-derivation | Hyperreal capture stats; gitignored `.reference-captures/linndrum/hyperreal/`. Needs re-derivation from that pack. |
| `minimoog.md` | L204#1 1. Filter slope is 24 dB/octave with resonance capable of full self-oscillation | traces | Qualitative literature criterion (Huovilainen DAFx-2004 PDF reached). No pack median. Pixabay and Perfect Circuit citations elsewhere in this dossier were HTTP 403 this session. |
| `minimoog.md` | L204#2 2. Filter saturates nonlinearly as resonance/drive increase, not a clean linear res | traces | Qualitative literature criterion (Huovilainen DAFx-2004 PDF reached). No pack median. Pixabay and Perfect Circuit citations elsewhere in this dossier were HTTP 403 this session. |
| `minimoog.md` | L204#3 3. Three-oscillator detune produces continuous chorusing rather than a fixed beat r | traces | Qualitative literature criterion (Huovilainen DAFx-2004 PDF reached). No pack median. Pixabay and Perfect Circuit citations elsewhere in this dossier were HTTP 403 this session. |
| `minimoog.md` | L204#4 4. Monophonic legato/glide behavior | traces | Already not adopted; sourced only to minimoog.py. Tell 4, already labeled. |
| `pianet.md` | L263#1 1. Timbre is nearly velocity-invariant | traces | Qualitative literature/guide criterion; no pack median. GregSullivan LICENSE is CC text (raw fetch) but that capture is the wrong model per §0 and was not used as a number here. |
| `pianet.md` | L263#2 2. Onset carries a brief unpitched "pluck-pop," not a thud | traces | Qualitative literature/guide criterion; no pack median. GregSullivan LICENSE is CC text (raw fetch) but that capture is the wrong model per §0 and was not used as a number here. |
| `pianet.md` | L263#3 3. Onset is harmonically complex, clears to a simpler tone within a fraction of a s | traces | Qualitative literature/guide criterion; no pack median. GregSullivan LICENSE is CC text (raw fetch) but that capture is the wrong model per §0 and was not used as a number here. |
| `pianet.md` | L263#4 4. Second-harmonic content is prominent — a "fuzz box"-like signature, not merely p | traces | Qualitative literature/guide criterion; no pack median. GregSullivan LICENSE is CC text (raw fetch) but that capture is the wrong model per §0 and was not used as a number here. |
| `pianet.md` | L263#5 5. Brighter/thinner in the octave or two above middle C than in the bass | traces | Qualitative literature/guide criterion; no pack median. GregSullivan LICENSE is CC text (raw fetch) but that capture is the wrong model per §0 and was not used as a number here. |
| `pianet.md` | L263#6 6. The note stops **dead** on release, not a fade, and a hold pedal makes no differ | traces | Qualitative literature/guide criterion; no pack median. GregSullivan LICENSE is CC text (raw fetch) but that capture is the wrong model per §0 and was not used as a number here. |
| `pianet.md` | L263#7 7. No hold-pedal (CC64) behavior exists or should exist | traces | Qualitative literature/guide criterion; no pack median. GregSullivan LICENSE is CC text (raw fetch) but that capture is the wrong model per §0 and was not used as a number here. |
| `polysix.md` | L301#1 1. Filter is a 4-pole (24 dB/oct) resonant low-pass, self-oscillating at high reson | traces | Literature from Korg owner's manual PDF (reached). wavparty license page reached; Producer Hive TOS reached as a Shopify terms page without a sample-pack license grant — matching the dossier's 'marketing bullet, not a license' call. |
| `polysix.md` | L301#2 2. EG (Attack/Decay/Release) ranges roughly 1 ms to 15+ s | traces | Literature from Korg owner's manual PDF (reached). wavparty license page reached; Producer Hive TOS reached as a Shopify terms page without a sample-pack license grant — matching the dossier's 'marketing bullet, not a license' call. |
| `polysix.md` | L301#3 3. Filter cutoff is EG-modulatable (±10 octaves) and keyboard-trackable (0–150%) | traces | Literature from Korg owner's manual PDF (reached). wavparty license page reached; Producer Hive TOS reached as a Shopify terms page without a sample-pack license grant — matching the dossier's 'marketing bullet, not a license' call. |
| `polysix.md` | L301#4 4. PWM is a genuine duty-cycle sweep, LFO-driven, speed-controllable, independent o | traces | Literature from Korg owner's manual PDF (reached). wavparty license page reached; Producer Hive TOS reached as a Shopify terms page without a sample-pack license grant — matching the dossier's 'marketing bullet, not a license' call. |
| `polysix.md` | L301#5 5. Sub-oscillator is a plain square wave, one or two octaves below, with a "wavefor | traces | Literature from Korg owner's manual PDF (reached). wavparty license page reached; Producer Hive TOS reached as a Shopify terms page without a sample-pack license grant — matching the dossier's 'marketing bullet, not a license' call. |
| `polysix.md` | L301#6 6. UNISON mode exists as a distinct, switchable, monophonic, 6-voice-detuned mode | traces | Literature from Korg owner's manual PDF (reached). wavparty license page reached; Producer Hive TOS reached as a Shopify terms page without a sample-pack license grant — matching the dossier's 'marketing bullet, not a license' call. |
| `polysix.md` | L301#7 7. MG (single LFO) is destination-selectable among VCO/VCF/VCA, not three simultane | traces | Literature from Korg owner's manual PDF (reached). wavparty license page reached; Producer Hive TOS reached as a Shopify terms page without a sample-pack license grant — matching the dossier's 'marketing bullet, not a license' call. |
| `rhodes.md` | L241#1 1. Fundamental pitch tracks MIDI note number (A440 reference, equal temperament) wi | traces | Qualitative proposed criterion; no pack median. Freesound 65762 reached and still shows Attribution 4.0. Pianobook FAQ reached and still states copyright-free for compositions, no library redistribution. |
| `rhodes.md` | L241#2 2. `Master Tune` macro range is a small detune, not a transposition | traces | Qualitative proposed criterion; no pack median. Freesound 65762 reached and still shows Attribution 4.0. Pianobook FAQ reached and still states copyright-free for compositions, no library redistribution. |
| `rhodes.md` | L241#3 3. Attack transient: is there a distinct unpitched "click" in the first ~5-10 ms, s | traces | Qualitative proposed criterion; no pack median. Freesound 65762 reached and still shows Attribution 4.0. Pianobook FAQ reached and still states copyright-free for compositions, no library redistribution. |
| `rhodes.md` | L241#4 4. Held-note envelope never plateaus at a nonzero level for the render's duration | traces | Qualitative proposed criterion; no pack median. Freesound 65762 reached and still shows Attribution 4.0. Pianobook FAQ reached and still states copyright-free for compositions, no library redistribution. |
| `rhodes.md` | L241#5 5. Spectral centroid / high-frequency content falls monotonically over the first ~1 | traces | Qualitative proposed criterion; no pack median. Freesound 65762 reached and still shows Attribution 4.0. Pianobook FAQ reached and still states copyright-free for compositions, no library redistribution. |
| `rhodes.md` | L241#6 6. Loudness-matched timbre changes with velocity ("the bark") — spectral shape (e.g | traces | Qualitative proposed criterion; no pack median. Freesound 65762 reached and still shows Attribution 4.0. Pianobook FAQ reached and still states copyright-free for compositions, no library redistribution. |
| `rhodes.md` | L241#7 7. Accented note peak stays under clipping at max velocity across the macro ranges | traces | Qualitative proposed criterion; no pack median. Freesound 65762 reached and still shows Attribution 4.0. Pianobook FAQ reached and still states copyright-free for compositions, no library redistribution. |
| `rhodes.md` | L241#8 8. 7+ simultaneous keys held: does the instrument silently drop notes below its own | traces | Qualitative proposed criterion; no pack median. Freesound 65762 reached and still shows Attribution 4.0. Pianobook FAQ reached and still states copyright-free for compositions, no library redistribution. |
| `rhodes.md` | L241#9 9. Key-off produces an audible, brief, unpitched "thud" distinct from the sustained | traces | Qualitative proposed criterion; no pack median. Freesound 65762 reached and still shows Attribution 4.0. Pianobook FAQ reached and still states copyright-free for compositions, no library redistribution. |
| `rhodes.md` | L241#10 10. Release-phase decay: does the tone stop within `Amp Release` rather than ringing | traces | Qualitative proposed criterion; no pack median. Freesound 65762 reached and still shows Attribution 4.0. Pianobook FAQ reached and still states copyright-free for compositions, no library redistribution. |
| `rhodes.md` | L241#11 11. Stereo tremolo: does `Tremolo Depth`/`Tremolo Rate` produce audible amplitude mo | traces | Qualitative proposed criterion; no pack median. Freesound 65762 reached and still shows Attribution 4.0. Pianobook FAQ reached and still states copyright-free for compositions, no library redistribution. |
| `simmons_sdsv.md` | L28#1 KickSimB | needs local re-derivation | SFM Sim-suffixed file stats; gitignored `.reference-captures/simmons_sdsv/`. Needs re-derivation from Free Drums From Mars. |
| `simmons_sdsv.md` | L28#2 KickSimG# | needs local re-derivation | SFM Sim-suffixed file stats; gitignored `.reference-captures/simmons_sdsv/`. Needs re-derivation from Free Drums From Mars. |
| `simmons_sdsv.md` | L28#3 SnareSim | needs local re-derivation | SFM Sim-suffixed file stats; gitignored `.reference-captures/simmons_sdsv/`. Needs re-derivation from Free Drums From Mars. |
| `simmons_sdsv.md` | L28#4 TomSim1 | needs local re-derivation | SFM Sim-suffixed file stats; gitignored `.reference-captures/simmons_sdsv/`. Needs re-derivation from Free Drums From Mars. |
| `simmons_sdsv.md` | L28#5 TomSim2 | needs local re-derivation | SFM Sim-suffixed file stats; gitignored `.reference-captures/simmons_sdsv/`. Needs re-derivation from Free Drums From Mars. |
| `simmons_sdsv.md` | L28#6 TomSim3 | needs local re-derivation | SFM Sim-suffixed file stats; gitignored `.reference-captures/simmons_sdsv/`. Needs re-derivation from Free Drums From Mars. |
| `simmons_sdsv.md` | L28#7 OHSim | needs local re-derivation | SFM Sim-suffixed file stats; gitignored `.reference-captures/simmons_sdsv/`. Needs re-derivation from Free Drums From Mars. |
| `simmons_sdsv.md` | L28#8 TomFXSim | needs local re-derivation | SFM Sim-suffixed file stats; gitignored `.reference-captures/simmons_sdsv/`. Needs re-derivation from Free Drums From Mars. |
| `simmons_sdsv.md` | L292#1 Bass Drum | needs local re-derivation | Measured tau/pitch from the same SFM json. Needs re-derivation from Free Drums From Mars. |
| `simmons_sdsv.md` | L292#2 Snare | needs local re-derivation | Tau from SFM json (needs local re-derivation). Pitch cell is literature-derived from the module's sd_pitch range (tell 4), already flagged unmeasurable. |
| `simmons_sdsv.md` | L292#3 Toms (pooled, identity unassigned) | needs local re-derivation | Measured tau/pitch from the same SFM json. Needs re-derivation from Free Drums From Mars. |
| `simmons_sdsv.md` | L292#4 Open Hat | needs local re-derivation | Measured tau/pitch from the same SFM json. Needs re-derivation from Free Drums From Mars. |
| `simmons_sdsv.md` | L301#1 Closed Hat | wording fixed | Already named as module-calibrated / no capture. Marker added this pass so it cannot be read as a pack figure. |
| `simmons_sdsv.md` | L301#2 Cymbal | wording fixed | Already named as module-calibrated / no capture. Marker added this pass so it cannot be read as a pack figure. |
| `sp1200-evidence.md` | L23#1 Bandwidth ceiling | traces | Literature targets from Yeh 2007 (PDF reached this session; 72-dB noise floor, 8-voice, 12-bit, 2/3× and 1.56× length, 13 kHz Nyquist all present in extracted text). Measured column is the model, not a pack median. |
| `sp1200-evidence.md` | L23#2 12-bit noise floor | traces | Literature targets from Yeh 2007 (PDF reached this session; 72-dB noise floor, 8-voice, 12-bit, 2/3× and 1.56× length, 13 kHz Nyquist all present in extracted text). Measured column is the model, not a pack median. |
| `sp1200-evidence.md` | L23#3 8-bit level DAC | traces | Literature targets from Yeh 2007 (PDF reached this session; 72-dB noise floor, 8-voice, 12-bit, 2/3× and 1.56× length, 13 kHz Nyquist all present in extracted text). Measured column is the model, not a pack median. |
| `sp1200-evidence.md` | L23#4 Pitch-tied decay | traces | Literature targets from Yeh 2007 (PDF reached this session; 72-dB noise floor, 8-voice, 12-bit, 2/3× and 1.56× length, 13 kHz Nyquist all present in extracted text). Measured column is the model, not a pack median. |
| `sp1200-evidence.md` | L23#5 VCF (SP Crunch) sweep | traces | Literature targets from Yeh 2007 (PDF reached this session; 72-dB noise floor, 8-voice, 12-bit, 2/3× and 1.56× length, 13 kHz Nyquist all present in extracted text). Measured column is the model, not a pack median. |
| `sp1200-evidence.md` | L23#6 Channel/filter routing | traces | Literature targets from Yeh 2007 (PDF reached this session; 72-dB noise floor, 8-voice, 12-bit, 2/3× and 1.56× length, 13 kHz Nyquist all present in extracted text). Measured column is the model, not a pack median. |
| `sp1200-evidence.md` | L23#7 Voice ceiling | traces | Literature targets from Yeh 2007 (PDF reached this session; 72-dB noise floor, 8-voice, 12-bit, 2/3× and 1.56× length, 13 kHz Nyquist all present in extracted text). Measured column is the model, not a pack median. |
| `sp1200.md` | L198#1 ~26.04 kHz effective bandwidth (Nyquist ≈13 kHz) | traces | Reachability/architecture row, not a pack median. Yeh PDF and service-manual metadata reached. |
| `sp1200.md` | L198#2 12-bit quantization noise floor (~72 dB SNR, Yeh) | traces | Reachability/architecture row, not a pack median. Yeh PDF and service-manual metadata reached. |
| `sp1200.md` | L198#3 8-bit level-DAC quantization (p.41) | traces | Reachability/architecture row, not a pack median. Yeh PDF and service-manual metadata reached. |
| `sp1200.md` | L198#4 Drop-sample pitch → decay-length coupling (Yeh §3.5, Figs. 6-7) | traces | Reachability/architecture row, not a pack median. Yeh PDF and service-manual metadata reached. |
| `sp1200.md` | L198#5 SSM2044 VCF: exponential cutoff sweep post-trigger, near-constant Q (Yeh §3.6) | traces | Reachability/architecture row, not a pack median. Yeh PDF and service-manual metadata reached. |
| `sp1200.md` | L198#6 True aliasing artifacts (spurious tones from the truncated-index skip/repeat and the zero- | traces | Reachability/architecture row, not a pack median. Yeh PDF and service-manual metadata reached. |
| `sp1200.md` | L264#1 Effective bandwidth ceiling | traces | Literature targets. Yeh PDF reached and still contains 72-dB noise floor, ~26 kHz fs, 2/3× and 1.56× length, 8-voice polyphony. Diggin It Samples Bandcamp HTTP 403 this session (not the source of these numbers). |
| `sp1200.md` | L264#2 Noise floor proxy | traces | Literature targets. Yeh PDF reached and still contains 72-dB noise floor, ~26 kHz fs, 2/3× and 1.56× length, 8-voice polyphony. Diggin It Samples Bandcamp HTTP 403 this session (not the source of these numbers). |
| `sp1200.md` | L264#3 Level quantization | traces | Literature targets. Yeh PDF reached and still contains 72-dB noise floor, ~26 kHz fs, 2/3× and 1.56× length, 8-voice polyphony. Diggin It Samples Bandcamp HTTP 403 this session (not the source of these numbers). |
| `sp1200.md` | L264#4 Pitch-tied decay length | traces | Literature targets. Yeh PDF reached and still contains 72-dB noise floor, ~26 kHz fs, 2/3× and 1.56× length, 8-voice polyphony. Diggin It Samples Bandcamp HTTP 403 this session (not the source of these numbers). |
| `sp1200.md` | L264#5 VCF (SP Crunch) sweep | traces | Literature targets. Yeh PDF reached and still contains 72-dB noise floor, ~26 kHz fs, 2/3× and 1.56× length, 8-voice polyphony. Diggin It Samples Bandcamp HTTP 403 this session (not the source of these numbers). |
| `sp1200.md` | L264#6 Channel/filter routing | traces | Literature targets. Yeh PDF reached and still contains 72-dB noise floor, ~26 kHz fs, 2/3× and 1.56× length, 8-voice polyphony. Diggin It Samples Bandcamp HTTP 403 this session (not the source of these numbers). |
| `sp1200.md` | L264#7 Voice ceiling | traces | Literature targets. Yeh PDF reached and still contains 72-dB noise floor, ~26 kHz fs, 2/3× and 1.56× length, 8-voice polyphony. Diggin It Samples Bandcamp HTTP 403 this session (not the source of these numbers). |
| `tb303.md` | L207#1 1. Oscillator: sawtooth **or** square, switchable | traces | Qualitative Wikipedia/Stinchcombe/service-notes criterion. Stinchcombe page reached. Oxide Sound Lab and SourceForge open303 License.txt were HTTP 403 this session (not the source of these rows). |
| `tb303.md` | L207#2 2. Filter: 24 dB/oct (4-pole) low-pass, non-self-oscillating, diode-ladder nonlinea | traces | Qualitative Wikipedia/Stinchcombe/service-notes criterion. Stinchcombe page reached. Oxide Sound Lab and SourceForge open303 License.txt were HTTP 403 this session (not the source of these rows). |
| `tb303.md` | L207#3 3. Envelope: fast, one-shot filter-cutoff sweep tied to the Decay control, plus an  | traces | Qualitative Wikipedia/Stinchcombe/service-notes criterion. Stinchcombe page reached. Oxide Sound Lab and SourceForge open303 License.txt were HTTP 403 this session (not the source of these rows). |
| `tb303.md` | L207#4 4. No onboard distortion/overdrive circuit in stock hardware; the classic "acid" gr | traces | Qualitative Wikipedia/Stinchcombe/service-notes criterion. Stinchcombe page reached. Oxide Sound Lab and SourceForge open303 License.txt were HTTP 403 this session (not the source of these rows). |
| `tr606.md` | L323#1 Voice/circuit structure | traces | Literature/structural. Baratatronix page reached and still states 7100 Hz and 3440 Hz. Polynominal TR-606 page reached. |
| `tr606.md` | L323#2 Tom choke | traces | Literature/structural. Baratatronix page reached and still states 7100 Hz and 3440 Hz. Polynominal TR-606 page reached. |
| `tr606.md` | L323#3 Hi-Hat choke | traces | Literature/structural. Baratatronix page reached and still states 7100 Hz and 3440 Hz. Polynominal TR-606 page reached. |
| `tr606.md` | L323#4 Cymbal/Hi-Hat noise bands | traces | Literature/structural. Baratatronix page reached and still states 7100 Hz and 3440 Hz. Polynominal TR-606 page reached. |
| `tr606.md` | L323#5 Open Hi-Hat decay | traces | Literature/structural. Baratatronix page reached and still states 7100 Hz and 3440 Hz. Polynominal TR-606 page reached. |
| `tr606.md` | L323#6 Bass Drum | traces | Literature/structural. Baratatronix page reached and still states 7100 Hz and 3440 Hz. Polynominal TR-606 page reached. |
| `tr707.md` | L274#1 Kick (BD1/BD2) | needs local re-derivation | Studio Brootle medians with n=; gitignored `.reference-captures/tr707/studio_brootle/`. Needs re-derivation from that pack. Bedroomproducersblog HTTP 403; ELPHNT zip host DNS failed; BØLT itch.io page reached with no license grant on the free tier. |
| `tr707.md` | L274#2 Snare (SD1/SD2) | needs local re-derivation | Studio Brootle medians with n=; gitignored `.reference-captures/tr707/studio_brootle/`. Needs re-derivation from that pack. Bedroomproducersblog HTTP 403; ELPHNT zip host DNS failed; BØLT itch.io page reached with no license grant on the free tier. |
| `tr707.md` | L274#3 Rim Shot | needs local re-derivation | Studio Brootle medians with n=; gitignored `.reference-captures/tr707/studio_brootle/`. Needs re-derivation from that pack. Bedroomproducersblog HTTP 403; ELPHNT zip host DNS failed; BØLT itch.io page reached with no license grant on the free tier. |
| `tr707.md` | L274#4 Cowbell | needs local re-derivation | Cowbell 0.040 s (n=2) from Studio Brootle. Note echoes tr808's 635 Hz cowbell target (tell 4 cross-dossier). Pack figure still needs local re-derivation; 635 Hz is not adopted as this row's number. |
| `tr707.md` | L274#5 Low Tom | needs local re-derivation | Studio Brootle medians with n=; gitignored `.reference-captures/tr707/studio_brootle/`. Needs re-derivation from that pack. Bedroomproducersblog HTTP 403; ELPHNT zip host DNS failed; BØLT itch.io page reached with no license grant on the free tier. |
| `tr707.md` | L274#6 Mid Tom | needs local re-derivation | Studio Brootle medians with n=; gitignored `.reference-captures/tr707/studio_brootle/`. Needs re-derivation from that pack. Bedroomproducersblog HTTP 403; ELPHNT zip host DNS failed; BØLT itch.io page reached with no license grant on the free tier. |
| `tr707.md` | L274#7 Hi Tom | needs local re-derivation | Studio Brootle medians with n=; gitignored `.reference-captures/tr707/studio_brootle/`. Needs re-derivation from that pack. Bedroomproducersblog HTTP 403; ELPHNT zip host DNS failed; BØLT itch.io page reached with no license grant on the free tier. |
| `tr707.md` | L274#8 Clap | needs local re-derivation | Studio Brootle medians with n=; gitignored `.reference-captures/tr707/studio_brootle/`. Needs re-derivation from that pack. Bedroomproducersblog HTTP 403; ELPHNT zip host DNS failed; BØLT itch.io page reached with no license grant on the free tier. |
| `tr707.md` | L274#9 Tambourine | needs local re-derivation | Studio Brootle medians with n=; gitignored `.reference-captures/tr707/studio_brootle/`. Needs re-derivation from that pack. Bedroomproducersblog HTTP 403; ELPHNT zip host DNS failed; BØLT itch.io page reached with no license grant on the free tier. |
| `tr707.md` | L274#10 Closed Hat | needs local re-derivation | Studio Brootle medians with n=; gitignored `.reference-captures/tr707/studio_brootle/`. Needs re-derivation from that pack. Bedroomproducersblog HTTP 403; ELPHNT zip host DNS failed; BØLT itch.io page reached with no license grant on the free tier. |
| `tr707.md` | L274#11 Open Hat | needs local re-derivation | Studio Brootle medians with n=; gitignored `.reference-captures/tr707/studio_brootle/`. Needs re-derivation from that pack. Bedroomproducersblog HTTP 403; ELPHNT zip host DNS failed; BØLT itch.io page reached with no license grant on the free tier. |
| `tr707.md` | L274#12 Crash | needs local re-derivation | Studio Brootle medians with n=; gitignored `.reference-captures/tr707/studio_brootle/`. Needs re-derivation from that pack. Bedroomproducersblog HTTP 403; ELPHNT zip host DNS failed; BØLT itch.io page reached with no license grant on the free tier. |
| `tr707.md` | L274#13 Ride | needs local re-derivation | Studio Brootle medians with n=; gitignored `.reference-captures/tr707/studio_brootle/`. Needs re-derivation from that pack. Bedroomproducersblog HTTP 403; ELPHNT zip host DNS failed; BØLT itch.io page reached with no license grant on the free tier. |
| `tr808-evidence.md` | L18#1 BD settled fundamental | needs local re-derivation | Target bands taken from tr808.md MusicRadar envelope. Pack json is gitignored. Needs re-derivation from the MusicRadar SampleRadar 808 pack. |
| `tr808-evidence.md` | L18#2 BD pitch trace | needs local re-derivation | Target bands taken from tr808.md MusicRadar envelope. Pack json is gitignored. Needs re-derivation from the MusicRadar SampleRadar 808 pack. |
| `tr808-evidence.md` | L18#3 BD decay macro span (τ at 0/127) | needs local re-derivation | Target bands taken from tr808.md MusicRadar envelope. Pack json is gitignored. Needs re-derivation from the MusicRadar SampleRadar 808 pack. |
| `tr808-evidence.md` | L18#4 SD τ / centroid | needs local re-derivation | Target bands taken from tr808.md MusicRadar envelope. Pack json is gitignored. Needs re-derivation from the MusicRadar SampleRadar 808 pack. |
| `tr808-evidence.md` | L18#5 CH τ / centroid | needs local re-derivation | Target bands taken from tr808.md MusicRadar envelope. Pack json is gitignored. Needs re-derivation from the MusicRadar SampleRadar 808 pack. |
| `tr808-evidence.md` | L18#6 OH τ | needs local re-derivation | Target bands taken from tr808.md MusicRadar envelope. Pack json is gitignored. Needs re-derivation from the MusicRadar SampleRadar 808 pack. |
| `tr808-evidence.md` | L18#7 Cymbal τ / f_early | needs local re-derivation | Target bands taken from tr808.md MusicRadar envelope. Pack json is gitignored. Needs re-derivation from the MusicRadar SampleRadar 808 pack. |
| `tr808-evidence.md` | L18#8 Cowbell f_early | needs local re-derivation | Target bands taken from tr808.md MusicRadar envelope. Pack json is gitignored. Needs re-derivation from the MusicRadar SampleRadar 808 pack. |
| `tr808-evidence.md` | L18#9 Toms pooled f_early | needs local re-derivation | Target bands taken from tr808.md MusicRadar envelope. Pack json is gitignored. Needs re-derivation from the MusicRadar SampleRadar 808 pack. |
| `tr808-evidence.md` | L18#10 Congas f_early | needs local re-derivation | Target bands taken from tr808.md MusicRadar envelope. Pack json is gitignored. Needs re-derivation from the MusicRadar SampleRadar 808 pack. |
| `tr808-evidence.md` | L18#11 Maracas τ / centroid | needs local re-derivation | Target bands taken from tr808.md MusicRadar envelope. Pack json is gitignored. Needs re-derivation from the MusicRadar SampleRadar 808 pack. |
| `tr808.md` | L151#1 1-2 kHz share | needs local re-derivation | Pack band-share (n=16). Gitignored MusicRadar json. Needs re-derivation from the MusicRadar SampleRadar 808 pack. §5a already records the 31.3/31.3 self-match; 2–4 kHz after 65.9% vs ref 63.9% is not same-decimal identity. |
| `tr808.md` | L151#2 2-4 kHz share | needs local re-derivation | Pack band-share (n=16). Gitignored MusicRadar json. Needs re-derivation from the MusicRadar SampleRadar 808 pack. §5a already records the 31.3/31.3 self-match; 2–4 kHz after 65.9% vs ref 63.9% is not same-decimal identity. |
| `tr808.md` | L151#3 4-8 kHz share | needs local re-derivation | Pack band-share (n=16). Gitignored MusicRadar json. Needs re-derivation from the MusicRadar SampleRadar 808 pack. §5a already records the 31.3/31.3 self-match; 2–4 kHz after 65.9% vs ref 63.9% is not same-decimal identity. |
| `tr808.md` | L151#4 8-24 kHz share | needs local re-derivation | Pack band-share (n=16). Gitignored MusicRadar json. Needs re-derivation from the MusicRadar SampleRadar 808 pack. §5a already records the 31.3/31.3 self-match; 2–4 kHz after 65.9% vs ref 63.9% is not same-decimal identity. |
| `tr808.md` | L151#5 centroid | needs local re-derivation | Pack band-share (n=16). Gitignored MusicRadar json. Needs re-derivation from the MusicRadar SampleRadar 808 pack. §5a already records the 31.3/31.3 self-match; 2–4 kHz after 65.9% vs ref 63.9% is not same-decimal identity. |
| `tr808.md` | L151#6 tau | needs local re-derivation | Pack band-share (n=16). Gitignored MusicRadar json. Needs re-derivation from the MusicRadar SampleRadar 808 pack. §5a already records the 31.3/31.3 self-match; 2–4 kHz after 65.9% vs ref 63.9% is not same-decimal identity. |
| `tr808.md` | L192#1 Rimshot tau | needs local re-derivation | TELL 1: after **27.1 ms** equals reference 27.1 ms (n=11) to the displayed decimal — the same class as the 31.3/31.3 cymbal share. Marker added. Do not treat as an independent pack confirmation until re-derived from the MusicRadar pack. |
| `tr808.md` | L192#2 Rimshot f_early / centroid | needs local re-derivation | MusicRadar pack figures (n=11/12). Gitignored json. Needs re-derivation from the MusicRadar SampleRadar 808 pack. |
| `tr808.md` | L192#3 Claves tau | needs local re-derivation | MusicRadar pack figures (n=11/12). Gitignored json. Needs re-derivation from the MusicRadar SampleRadar 808 pack. |
| `tr808.md` | L192#4 Low Tom f_early | needs local re-derivation | MusicRadar pack figures (n=11/12). Gitignored json. Needs re-derivation from the MusicRadar SampleRadar 808 pack. |
| `tr808.md` | L192#5 Mid Tom f_early | needs local re-derivation | MusicRadar pack figures (n=11/12). Gitignored json. Needs re-derivation from the MusicRadar SampleRadar 808 pack. |
| `tr808.md` | L192#6 Hi Tom f_early | needs local re-derivation | MusicRadar pack figures (n=11/12). Gitignored json. Needs re-derivation from the MusicRadar SampleRadar 808 pack. |
| `tr808.md` | L239#1 BD attack | needs local re-derivation | Acceptance targets from MusicRadar json. Gitignored. Needs re-derivation from that pack. Several rows also lack n=/IQR in the cell (tell 2) even though the section names the pack. |
| `tr808.md` | L239#2 BD settled fundamental | needs local re-derivation | Acceptance targets from MusicRadar json. Gitignored. Needs re-derivation from that pack. Several rows also lack n=/IQR in the cell (tell 2) even though the section names the pack. |
| `tr808.md` | L239#3 BD decay tau, short setting | needs local re-derivation | Acceptance targets from MusicRadar json. Gitignored. Needs re-derivation from that pack. Several rows also lack n=/IQR in the cell (tell 2) even though the section names the pack. |
| `tr808.md` | L239#4 BD decay tau, long setting | needs local re-derivation | Acceptance targets from MusicRadar json. Gitignored. Needs re-derivation from that pack. Several rows also lack n=/IQR in the cell (tell 2) even though the section names the pack. |
| `tr808.md` | L239#5 SD tau / centroid | needs local re-derivation | SD 0.042 s / 4494 Hz: named MusicRadar section but no n=/IQR in the cell (tell 2). Gitignored json. Needs re-derivation from the MusicRadar pack. |
| `tr808.md` | L239#6 CH tau / centroid | needs local re-derivation | CH 0.024 s / 9687 Hz: no n=/IQR in the cell (tell 2). Gitignored json. Needs re-derivation from the MusicRadar pack. |
| `tr808.md` | L239#7 OH tau | needs local re-derivation | OH tau 0.173 s: no n=/IQR in the cell (tell 2). Gitignored json. Needs re-derivation from the MusicRadar pack. |
| `tr808.md` | L239#8 Cymbal tau / f_early | needs local re-derivation | Cymbal tau/f_early 0.775 s / 7752 Hz: no n=/IQR in the cell (tell 2). Gitignored json. Needs re-derivation from the MusicRadar pack. |
| `tr808.md` | L239#9 Cowbell f_early | needs local re-derivation | Cowbell f_early 635 Hz: no n=/IQR in the cell (tell 2). Gitignored json. Needs re-derivation from the MusicRadar pack. |
| `tr808.md` | L239#10 Rimshot tau / f_early / centroid | needs local re-derivation | Acceptance targets from MusicRadar json. Gitignored. Needs re-derivation from that pack. Several rows also lack n=/IQR in the cell (tell 2) even though the section names the pack. |
| `tr808.md` | L239#11 Claves tau / f_early / centroid | needs local re-derivation | Acceptance targets from MusicRadar json. Gitignored. Needs re-derivation from that pack. Several rows also lack n=/IQR in the cell (tell 2) even though the section names the pack. |
| `tr808.md` | L239#12 Low Tom f_early | needs local re-derivation | Acceptance targets from MusicRadar json. Gitignored. Needs re-derivation from that pack. Several rows also lack n=/IQR in the cell (tell 2) even though the section names the pack. |
| `tr808.md` | L239#13 Mid Tom f_early | needs local re-derivation | Acceptance targets from MusicRadar json. Gitignored. Needs re-derivation from that pack. Several rows also lack n=/IQR in the cell (tell 2) even though the section names the pack. |
| `tr808.md` | L239#14 Hi Tom f_early | needs local re-derivation | Acceptance targets from MusicRadar json. Gitignored. Needs re-derivation from that pack. Several rows also lack n=/IQR in the cell (tell 2) even though the section names the pack. |
| `tr808.md` | L239#15 Conga Lo f_early | needs local re-derivation | Acceptance targets from MusicRadar json. Gitignored. Needs re-derivation from that pack. Several rows also lack n=/IQR in the cell (tell 2) even though the section names the pack. |
| `tr808.md` | L239#16 Conga Mid f_early | needs local re-derivation | Maracas 0.033 s / 7658 Hz: no n=/IQR in the cell (tell 2). Gitignored json. Needs re-derivation from the MusicRadar pack. |
| `tr808.md` | L239#17 Conga Hi f_early | needs local re-derivation | Acceptance targets from MusicRadar json. Gitignored. Needs re-derivation from that pack. Several rows also lack n=/IQR in the cell (tell 2) even though the section names the pack. |
| `tr808.md` | L239#18 Maracas tau / centroid | needs local re-derivation | Acceptance targets from MusicRadar json. Gitignored. Needs re-derivation from that pack. Several rows also lack n=/IQR in the cell (tell 2) even though the section names the pack. |
| `tr808.md` | L239#19 CH loudness | needs local re-derivation | Acceptance targets from MusicRadar json. Gitignored. Needs re-derivation from that pack. Several rows also lack n=/IQR in the cell (tell 2) even though the section names the pack. |
| `tr808.md` | L239#20 OH loudness | needs local re-derivation | Acceptance targets from MusicRadar json. Gitignored. Needs re-derivation from that pack. Several rows also lack n=/IQR in the cell (tell 2) even though the section names the pack. |
| `tr808.md` | L239#21 Cymbal loudness | needs local re-derivation | Acceptance targets from MusicRadar json. Gitignored. Needs re-derivation from that pack. Several rows also lack n=/IQR in the cell (tell 2) even though the section names the pack. |
| `tr808.md` | L239#22 Accented solo peak, any voice | needs local re-derivation | Acceptance targets from MusicRadar json. Gitignored. Needs re-derivation from that pack. Several rows also lack n=/IQR in the cell (tell 2) even though the section names the pack. |
| `tr808.md` | L270#1 Hi Tom | traces | Historical arithmetic showing why pooled tom/conga rows failed; not a current reference target. |
| `tr808.md` | L270#2 Conga Hi | traces | Historical arithmetic showing why pooled tom/conga rows failed; not a current reference target. |
| `tr808.md` | L419#1 CH before | needs local re-derivation | CH/OH/CY reference cells are pack medians from MusicRadar json. Gitignored. Needs re-derivation from that pack. Before/after cells are the model. |
| `tr808.md` | L419#2 CH after | needs local re-derivation | CH/OH/CY reference cells are pack medians from MusicRadar json. Gitignored. Needs re-derivation from that pack. Before/after cells are the model. |
| `tr808.md` | L419#3 CH reference | needs local re-derivation | CH/OH/CY reference cells are pack medians from MusicRadar json. Gitignored. Needs re-derivation from that pack. Before/after cells are the model. |
| `tr808.md` | L419#4 OH before | needs local re-derivation | CH/OH/CY reference cells are pack medians from MusicRadar json. Gitignored. Needs re-derivation from that pack. Before/after cells are the model. |
| `tr808.md` | L419#5 OH after | needs local re-derivation | CH/OH/CY reference cells are pack medians from MusicRadar json. Gitignored. Needs re-derivation from that pack. Before/after cells are the model. |
| `tr808.md` | L419#6 OH reference | needs local re-derivation | CH/OH/CY reference cells are pack medians from MusicRadar json. Gitignored. Needs re-derivation from that pack. Before/after cells are the model. |
| `tr808.md` | L419#7 CY before | needs local re-derivation | CH/OH/CY reference cells are pack medians from MusicRadar json. Gitignored. Needs re-derivation from that pack. Before/after cells are the model. |
| `tr808.md` | L419#8 CY after | needs local re-derivation | CH/OH/CY reference cells are pack medians from MusicRadar json. Gitignored. Needs re-derivation from that pack. Before/after cells are the model. |
| `tr808.md` | L419#9 CY reference | needs local re-derivation | CH/OH/CY reference cells are pack medians from MusicRadar json. Gitignored. Needs re-derivation from that pack. Before/after cells are the model. |
| `tr909-evidence.md` | L13#1 BD Tune settled | needs local re-derivation | Hardware column from Audiorealism pack grids. Gitignored `.reference-captures/tr909/`. Rebuild column is the model and is not same-decimal identical to hardware (BD Tune 46.9→82.0 vs 46.4→84.1). Needs re-derivation of the hardware column from the pack. |
| `tr909-evidence.md` | L13#2 BD Decay tau | needs local re-derivation | Hardware column from Audiorealism pack grids. Gitignored `.reference-captures/tr909/`. Rebuild column is the model and is not same-decimal identical to hardware (BD Tune 46.9→82.0 vs 46.4→84.1). Needs re-derivation of the hardware column from the pack. |
| `tr909-evidence.md` | L13#3 BD Attack onset | needs local re-derivation | Hardware column from Audiorealism pack grids. Gitignored `.reference-captures/tr909/`. Rebuild column is the model and is not same-decimal identical to hardware (BD Tune 46.9→82.0 vs 46.4→84.1). Needs re-derivation of the hardware column from the pack. |
| `tr909-evidence.md` | L13#4 SD Tune f_early | needs local re-derivation | Hardware column from Audiorealism pack grids. Gitignored `.reference-captures/tr909/`. Rebuild column is the model and is not same-decimal identical to hardware (BD Tune 46.9→82.0 vs 46.4→84.1). Needs re-derivation of the hardware column from the pack. |
| `tr909-evidence.md` | L13#5 Tom Decay (LT) tau | needs local re-derivation | Hardware column from Audiorealism pack grids. Gitignored `.reference-captures/tr909/`. Rebuild column is the model and is not same-decimal identical to hardware (BD Tune 46.9→82.0 vs 46.4→84.1). Needs re-derivation of the hardware column from the pack. |
| `tr909-evidence.md` | L13#6 Cymbal Tune → Ride tau (inverse) | needs local re-derivation | Hardware column from Audiorealism pack grids. Gitignored `.reference-captures/tr909/`. Rebuild column is the model and is not same-decimal identical to hardware (BD Tune 46.9→82.0 vs 46.4→84.1). Needs re-derivation of the hardware column from the pack. |
| `tr909.md` | L186#1 Low | traces | Header names this as the module's own macro range, not a pack reference. Tell 4, already labeled. |
| `tr909.md` | L186#2 Mid | traces | Header names this as the module's own macro range, not a pack reference. Tell 4, already labeled. |
| `tr909.md` | L186#3 Hi | traces | Header names this as the module's own macro range, not a pack reference. Tell 4, already labeled. |
| `tr909.md` | L284#1 Bass Drum | needs local re-derivation | Aggregate medians from 848-hit Audiorealism json. No n=/IQR in the cells (tell 2). Gitignored. Needs re-derivation from the Audiorealism TR-909 pack. Included Readme.txt (the actual license) not opened this session (gitignored zip). |
| `tr909.md` | L284#2 Snare Drum | needs local re-derivation | Aggregate medians from 848-hit Audiorealism json. No n=/IQR in the cells (tell 2). Gitignored. Needs re-derivation from the Audiorealism TR-909 pack. Included Readme.txt (the actual license) not opened this session (gitignored zip). |
| `tr909.md` | L284#3 Closed Hat | needs local re-derivation | Aggregate medians from 848-hit Audiorealism json. No n=/IQR in the cells (tell 2). Gitignored. Needs re-derivation from the Audiorealism TR-909 pack. Included Readme.txt (the actual license) not opened this session (gitignored zip). |
| `tr909.md` | L284#4 Open Hat | needs local re-derivation | Aggregate medians from 848-hit Audiorealism json. No n=/IQR in the cells (tell 2). Gitignored. Needs re-derivation from the Audiorealism TR-909 pack. Included Readme.txt (the actual license) not opened this session (gitignored zip). |
| `tr909.md` | L284#5 Low/Mid/Hi Tom (pooled) | needs local re-derivation | Pooled Low/Mid/Hi Tom 0.072–0.103 / 1608 Hz: one band standing for three pitches — same class of criterion the tr808 pooled rows were retired for. Not recomputed. Needs per-pitch re-derivation from the Audiorealism pack. |
| `tr909.md` | L284#6 Rimshot | needs local re-derivation | Aggregate medians from 848-hit Audiorealism json. No n=/IQR in the cells (tell 2). Gitignored. Needs re-derivation from the Audiorealism TR-909 pack. Included Readme.txt (the actual license) not opened this session (gitignored zip). |
| `tr909.md` | L284#7 Hand Clap | needs local re-derivation | Aggregate medians from 848-hit Audiorealism json. No n=/IQR in the cells (tell 2). Gitignored. Needs re-derivation from the Audiorealism TR-909 pack. Included Readme.txt (the actual license) not opened this session (gitignored zip). |
| `tr909.md` | L284#8 Crash | needs local re-derivation | Aggregate medians from 848-hit Audiorealism json. No n=/IQR in the cells (tell 2). Gitignored. Needs re-derivation from the Audiorealism TR-909 pack. Included Readme.txt (the actual license) not opened this session (gitignored zip). |
| `tr909.md` | L284#9 Ride | needs local re-derivation | Aggregate medians from 848-hit Audiorealism json. No n=/IQR in the cells (tell 2). Gitignored. Needs re-derivation from the Audiorealism TR-909 pack. Included Readme.txt (the actual license) not opened this session (gitignored zip). |
| `tr909.md` | L301#1 BD Tune (settled, 40-80ms post-peak) | needs local re-derivation | Knob curves from gitignored knob_curves.json. Needs re-derivation from the Audiorealism pack. |
| `tr909.md` | L301#2 BD Decay (tau) | needs local re-derivation | Knob curves from gitignored knob_curves.json. Needs re-derivation from the Audiorealism pack. |
| `tr909.md` | L301#3 BD Attack (onset peak dBFS) | needs local re-derivation | Knob curves from gitignored knob_curves.json. Needs re-derivation from the Audiorealism pack. |
| `tr909.md` | L301#4 SD Tune (f_early) | needs local re-derivation | Knob curves from gitignored knob_curves.json. Needs re-derivation from the Audiorealism pack. |
| `tr909.md` | L301#5 Tom Decay, Low Tom (tau) | needs local re-derivation | Knob curves from gitignored knob_curves.json. Needs re-derivation from the Audiorealism pack. |
| `tr909.md` | L301#6 Cymbal Tune, Ride (tau, inverse) | needs local re-derivation | Knob curves from gitignored knob_curves.json. Needs re-derivation from the Audiorealism pack. |
| `wurlitzer.md` | L287#1 1. Fundamental pitch tracks MIDI note × `Master Tune` | traces | Qualitative / self-consistency criterion. Row 2 already records the /127* linear-grid correction; DAFx-17 PDF reached. No pack median. |
| `wurlitzer.md` | L287#2 2. Attack is fast and reed-like | traces | No numeric hardware target sourced. Historical `/127*` formula is quoted only inside the 2026-09-03 correction. Mechanical grep hit lives here; live mapping is logmap(47/127, 0.001, 0.501). |
| `wurlitzer.md` | L287#3 3. Velocity moves both level *and* brightness together (the "bark") | traces | Qualitative / self-consistency criterion. Row 2 already records the /127* linear-grid correction; DAFx-17 PDF reached. No pack median. |
| `wurlitzer.md` | L287#4 4. Bite decays out faster than the body, independent of the `Amp Decay` macro | traces | Qualitative / self-consistency criterion. Row 2 already records the /127* linear-grid correction; DAFx-17 PDF reached. No pack median. |
| `wurlitzer.md` | L287#5 5. Tremolo modulates loudness only, never pitch | traces | Qualitative / self-consistency criterion. Row 2 already records the /127* linear-grid correction; DAFx-17 PDF reached. No pack median. |
| `wurlitzer.md` | L287#6 6. Held note continues to lose energy rather than plateauing forever | traces | Qualitative / self-consistency criterion. Row 2 already records the /127* linear-grid correction; DAFx-17 PDF reached. No pack median. |
| `wurlitzer.md` | L287#7 7. Release/damping character after key-up | traces | Qualitative / self-consistency criterion. Row 2 already records the /127* linear-grid correction; DAFx-17 PDF reached. No pack median. |
| `wurlitzer.md` | L287#8 8. Whether a hard-struck note's bark genuinely "melts" into the sweet tail as it ri | traces | Qualitative / self-consistency criterion. Row 2 already records the /127* linear-grid correction; DAFx-17 PDF reached. No pack median. |

**Table totals:** traces 137, wording fixed 2, needs local re-derivation 128, source not reached 0. Sum 267 (classifier 267).
