"""`Saturation` - a 12AX7 stage, a tape chain, or transformer iron.

Rebuilt from scratch for Phase 4 against
`workspace docs/effects-internal/dossiers/Saturation.md`, traits frozen at
Station A on 2026-09-17 before this file existed. The old `drive.py:Saturation`
is not consulted except for the six defects the dossier's section 7 names,
and it stays the class the library serves until the auditor adopts this one.

**What it sounds like.** `tube` (default) is a 12AX7 common-cathode stage:
even harmonics below 0.5 V grid, a hard plate ceiling one way and grid
conduction the other. `tape` is a reel-to-reel chain: odd Langevin
saturation and a playback-loss curve that slides with Speed. `console` is
transformer iron: flux-driven, saturating from the bottom up.

All three are AC-coupled after the shaping, at 20 Hz — the plate coupling
capacitor, the playback head that cannot see DC, the flux high-pass. That
is where Bias's operating-point shift goes instead of onto the output.

**What the default surrenders.** Mix 1, Drive 0 dB, Headroom 0, Bias 0,
Tilt 0, Hysteresis 0, Speed 15 ips (inert on tube).

**Headroom is Drive, spent the other way round, and they share one
ceiling.** Headroom moves the character's knee and Drive moves the signal
at it; in front of one curve on one node that is a single number. It used
to be two — `pre = pre0·drive/head` — which gave the pair **+27 dB** of
reach behind a documented **+15 dB** cap, and the alias floor failed from
the shipped surface at Headroom −6 / Output +6 (**−45.621 dB** at 3700 Hz,
audiocomponents#70). **Drive − Headroom stops at +15 dB** however you
reach it: that is where the floor still holds 60 dB down at 1010 and
3700 Hz (−70.6 / −63.8 at 48 kHz). It costs the top of the range and the
plate has long since pinned by then.

**The alias floor is a ratio, and 16 bits is not.** It is claimed at
48 kHz, on `tube`, at the class's own output level. Wherever the output is
quiet the ratio reads badly whatever the shaper did, one dB for one:
Output −12 / −18 / −24 read **−69.007 / −63.233 / −57.301**, and
`character="console"` reads **−46.094** at Drive 0 because its 5 Hz flux
pair takes 25 dB out before the jack. Bias past ±0.25 walks the stage to
cutoff or into grid conduction and the floor goes with it (**−47.491** at
+0.25, −27.136 at +1); the shipped patches use ±0.1, which reads −64.160.
Over the whole Drive × Headroom plane at 48 kHz the worst cell is
**−63.863** (3700 Hz, maximum Drive, Headroom −3) and every cell clears.
**At 44.1 kHz the 3700 Hz probe cannot reach the bar at any factor**
(−47.763 at maximum Drive, **−41.880** at the plane's worst): h6 of
3700 Hz is above that rate's Nyquist and folds back whatever the internal
rate was. **At 22.05 kHz it misses at the shipped default** (−58.181) and
reads **−17.591** at maximum Drive, because h3 is already above Nyquist
there. The dossier does not claim 22.05 kHz; this says so out loud.

**The even lead holds from 0.05 V to 0.5 V of grid, not below.** Under the
freeze's own quietest probe the table runs out: at 0.0316 V the h2−h3 lead
is **7.294 dB** and at 0.0089 V it is **−15.049** (48 kHz). One table cell
is 0.0195 V of grid, so a 0.0089 V peak sweeps less than half a cell and
what h2 reports there is interpolation residue, not a triode. Worst cell
inside the bound, over 63 (level, rate) cells: **16.008 dB**.

The Hysteresis macro is off; TP3 is not a graded trait (dossier §8 Q1).
Drive compensation keeps small-signal level from jumping with the knob.
Switching into or out of patch 8 re-routes the pull chain, so it steps at
the block boundary like the patch change it is (3357 LSB against 1281 for
an ordinary patch change on the same material) — a setup choice, not a
knob to ride.

**Portability tier: audioif** (`REQUIRES = ("audioshaper", "audiobiquad",
"audioroute", "audioecho")`). On a stock CircuitPython board this module
imports and construction raises `ImportError`.

**The rate picks the oversampling factor**, on the measurement in
`OVERSAMPLE_RATE_HZ`: **×4 at 48 and 44.1 kHz, ×2 at 22.05 kHz.** ×8 was
shipped everywhere and bought nothing at the default — ×1 and ×4 are
within 2 dB there (−76.806 against −77.693 at 1010 Hz) — while costing the
S3 1.408 ms a block. At maximum Drive, where it is the oversampler's fold
to lose, ×4 clears the bar (−63.847 at 3700 Hz) and ×8 adds 0.923 dB.

**Cost, palette, reference patch 0 (tube, 48 kHz, oversample ×4)**, priced
at the rows both boards took on 2026-09-18:
Splitter-2 0.207/0.368 + Waveshaper ×4 1.069/1.918 + 3×Biquad 0.324/0.612
+ Mixer 0.050/0.175 + glue 0.0
= **1.650 / 3.073 ms → P4 31 %, S3 58 %** of a 5.333 ms stereo block.
**Three biquads and not four**: `_after` *is* `_couple` on `tube` and
`tape`, so the board's attribute census counted one node under two names.
The boards measured **34.3 % / 62.2 %** — **over by 3.4 / 4.6 points**, and
the node count is not what is over. Every node the class drops leaves the
sum by exactly its palette row, so the miss is the same afterwards: what is
over is the **per-block glue** every budget in this program prices at 0.0.
The class handed back a **128-frame** block (`Mixer._render_size` is
`buffer_size // 2 // 4 * 4` bytes), so everything behind it was pulled twice
per 256-frame block, and one extra Python-level pull is worth about
**0.18 ms on the P4 and 0.11 ms on the S3** — read off the boards' own rows,
`Splitter+3 − Splitter+tap` (an extra tap pulled from Python) against
`Mixer@3active − Mixer@2active` (the same extra tap pulled from C). On the
P4 that is the whole 3.4 points. `MIXER_BUFFER_BYTES × channel_count` makes
one pull one block and **moves no byte**: `ffb5e07e33e2732d` at patch 0 and
`58444f96ff950621` at patch 8, at either block length, on CPython,
MicroPython and CircuitPython. **The second board pass measured that graph
on 2026-09-18 and the miss is gone**: 29.4 % / 55.4 % at patch 0, 20.8 % /
39.6 % at patch 8, 29.9 % / 56.4 % at its costliest patch.

**Alone on an ESP32-S3 this uses 55 % of a block at its default patch,
56 % at its costliest; use patch 8 `Saturation - lean` (40 %) to stack.**

At 22.05 kHz the block is 11.61 ms and ×2 prices at
1.139 / 2.172 ms, **10 % / 19 %**.
The identity `MidSide` tail is gone: it was there so the class would not end
on a Mixer, and what it bought instead was an LSB on every full-scale sample
(audioif#95). At Mix 0 the output **is** the borrowed source, so the wire is
exact by construction and nothing in the graph is pulled at all.
Patch 8 `Saturation - lean` is one factor below whatever the rate ships —
×2 at 48 kHz, through a second node nothing else pulls: Waveshaper ×2
0.558/1.017 + the same rest = **1.139 / 2.172 ms → 21 % / 41 %**, measured
**24.7 % / 46.4 %**, which is the same glue over the same graph. It buys
that partly out of the floor and the pack says so: 1010 Hz still clears at
maximum Drive, 3700 Hz reads **−56.686** and does not.
`hysteresis` has no palette row (gap). The silence sample is pulled once,
at construction, so it is not a source row. `tape` adds a fourth biquad for
the playback loss — 1.758 / 3.277 ms, **33 % / 61 %** — and `console`
replaces one biquad with two bare FeedbackDelay rows, which have no Phase 4
row at all. Neither is this bar.

**Latency — one reading, said plainly.** There were two, and the class
declared a third: `_GROUP_DELAY_SAMPLES` is where the half-band's
*centroid* sits, and the onset of a symmetric response arrives **before**
its centroid, so `tube` graded sub-sample and failed the integer onset by
2 samples while `console` did the opposite — **10 of 18 build × rate
cells red** (audit 3 (p)8). `latency_samples` is the **measured integer
onset** now, per character and factor (`CLICK_ONSET_SAMPLES`), which is
the reading a host's delay compensation can use and the one `Distortion`
already declares: **tube 1 / tape 2 / console 4** at the shipped ×4,
**0 / 1 / 3** at ×2, **2 / 2 / 5** at ×8, and 0 / 0 / 2 at ×1. Mix 0 is a
dry tap and reports **0**. All 18 build × rate cells now read within the
kit's 1-sample bar, stereo and mono.

The sub-sample reading is the graph's own group delay and is **not** what
this reports: 3.912 samples at tube ×4, 4.753 at tape, 6.418 at console,
and on `console` it is probe-dependent besides — 12.774 on an impulse and
16.808 on a 4 ms burst, which is the 5 Hz damping and cut filters inside
its two flux sections (`kit.click`'s own words).

**Output is decibels out for decibels asked, and there is a makeup stage
behind the shaper.** What the node gives up at `NODE_CEILING` used to go
onto the wet mixer voice as `level > 1.0` — and **a mixer voice clamps at
1.0**, so Output +6 delivered **+5.965 dB** and Output +12 delivered
**+7.866** (1 kHz, −12 dBFS), while the test that should have caught it
multiplied two numbers in Python and never rendered (audit 3 (p)1, ruling
(o)). `MAKEUP_SHELF_HZ` is a `HIGH_SHELF` at 10 Hz — flat everywhere a
note lives, 0.02 dB down at 100 Hz — and it carries the excess. Rendered,
+3 / +6 / +9 / +12 dB of Output now deliver within **0.25 dB** of what
they say, on `tube` and on `console`. It is 0 dB at 63 of the 75 shipped
positions, whose bytes do not move.

**The tube table does not invert any more.** A triode inverts, and a table
that carried the inversion put the wet leg 180° out of phase with the dry
one, so **Mix was a notch rather than a blend**: rendered at −12 dBFS the
level walked −15.011 → −18.609 → −24.676 → **−33.580** → −23.125 dBFS
across Mix 0 … 1, with the deepest point three quarters of the way up
(audit 3 (p)2). Every unit this models has an even number of gain stages
for exactly that reason, so the sign moved into
`saturation_curve.tube_points()` and no harmonic magnitude moved with it.
Mix now walks −15.011 → −16.515 → −18.301 → −20.469 → −23.125.

**The plate coupling pole is charged before the first block.** `Bias` is
an offset into an asymmetric curve, so the shaper answers silence with a
constant and the pole behind it blocked the constant but not the step:
shipped patches 4 and 6 put **8 489 and 7 044 LSB** out of digital
silence. They put **1 LSB** now. A live Bias move is not re-charged — the
wet leg comes off a `Splitter` — and settles through the pole instead;
Bias +0.30 still settles to a **−5 LSB** floor and Bias +1.0 to −11, which
is the class's stated residual and is what `±1 LSB at the input of this
much gain` looks like at the steepest part of the curve.

**Tail.** `TAIL_SAMPLES = 65536` (1.365 s at 48 kHz), measured: a 200 ms
0 dBFS burst's residual reaches 0 LSB **3282 frames** after the burst on
`tube`, 3196 on `tape` and **13759 on `console`**, whose flux corner is at
5 Hz. The 655360 it used to declare was 13.65 s and was in neither the
pack nor a measurement. **Those are 1 kHz numbers**: a 40 Hz burst on
`console` reads **19 317** frames, so the declaration is 3.4× the worst
measured and not the 4.8× the pack claimed (audit 3 (p)7).

**Insertion loss, which no row carried.** At the default, a −12 dBFS
1 kHz sine comes out **8.1 dB** down on `tube`, **13.4** on `tape` and
**33.6** on `console`. That is the unit's own gain structure — a saturator
is a gain stage followed by a ceiling — and `Output` is what puts it
back, but a row that says nothing about it leaves a user thinking Mix 1 is
unity. It is not.

`capabilities = ()`: nothing reads `self._transport()`.
"""

VENDOR = "PyDevices"

from array import array
import math

try:
    import audiobiquad
except ImportError:                     # pragma: no cover - a stock board
    audiobiquad = None
try:
    import audioshaper
except ImportError:
    audioshaper = None
try:
    import audioroute
except ImportError:
    audioroute = None
try:
    import audioecho
except ImportError:
    audioecho = None

import audiocore
import audiomixer

try:
    from audioif_util import float32 as _f32
except ImportError:                                  # pragma: no cover
    def _f32(value):
        return value

from .. import _component


# --- BEGIN TUBE_CURVE ---
TUBE_CURVE = bytes.fromhex(
    "e19ae19ae19ae19ae19ae19ae19ae19ae19ae19ae19ae19ae19ae19ae19ae19a" +
    "e19ae19ae19ae19ae19ae19ae19ae19ae19ae19ae19ae19ae19ae19ae19ae19a" +
    "e19ae19ae19ae19ae19ae19ae19ae19ae19ae19ae19ae19ae19ae19ae19ae19a" +
    "e19ae19ae19ae19ae19ae19ae19ae19ae19ae19ae19ae19ae19ae19ae19ae19a" +
    "e19ae19ae19ae19ae19ae19ae19ae19ae19ae19ae19ae19ae19ae19ae19ae19a" +
    "e19ae19ae19ae19ae19ae19ae19ae19ae19ae19ae19ae19ae19ae19ae19ae19a" +
    "e19ae19ae19ae19ae19ae19ae19ae19ae19ae19ae19ae19ae19ae19ae19ae19a" +
    "e19ae19ae19ae19ae19ae19ae19ae19ae19ae19ae19ae19ae19ae19ae19ae19a" +
    "e19ae19ae19ae19ae19ae19ae19ae19ae19ae19ae19ae19ae19ae19ae19ae19a" +
    "e19ae19ae19ae19ae19ae19ae19ae19ae19ae19ae19ae19ae19ae19ae19ae19a" +
    "e19ae19ae19ae19ae19ae19ae19ae19ae19ae19ae19ae19ae19ae19ae19ae19a" +
    "e19ae19ae19ae19ae19ae19ae19ae19ae19ae19ae19ae19ae19ae19ae19ae19a" +
    "e19ae19ae19ae19ae19ae19ae19ae19ae19ae19ae19ae19ae19ae19ae19ae19a" +
    "e19ae19ae19ae19ae19ae19ae19ae19ae19ae19ae19ae19ae19ae19ae19ae19a" +
    "e19ae19ae19ae19ae19ae19ae19ae19ae19ae19ae19ae19ae19ae19ae19ae19a" +
    "e19ae19ae19ae19ae19ae19ae19ae19ae19ae19ae19ae19ae19ae19ae19ae19a" +
    "e19ae19ae19ae19ae19ae19ae19ae19ae19ae19ae19ae19ae19ae19ae19ae19a" +
    "e19ae19ae19ae19ae19ae19ae19ae19ae19ae19ae19ae19ae19ae19ae19ae19a" +
    "e19ae19ae19ae19ae19ae19ae19ae19ae19ae19ae19ae19ae19ae19ae19ae19a" +
    "e19ae19ae19ae19ae19ae19ae19ae19ae19ae19ae19ae19ae19ae19ae19ae19a" +
    "e19ae19ae19ae19ae19ae19ae19ae19ae19ae19ae19ae19ae19ae19ae19ae19a" +
    "e19ae19ae19ae19ae19ae19ae19ae19ae19ae19ae19ae19ae19ae19ae19ae19a" +
    "e29ae29ae29ae39ae39ae39ae49ae49ae59ae69ae69ae79ae89ae99aea9aeb9a" +
    "ec9aed9aee9aef9af19af39af49af69af89afb9afd9a009b039b069b099b0d9b" +
    "119b159b1a9b1f9b259b2b9b329b399b409b499b529b5c9b669b729b7e9b8c9b" +
    "9a9baa9bbb9bce9be19bf79b0e9c279c419c5e9c7d9c9e9cc29ce89c119d3d9d" +
    "6c9d9e9dd49d0d9e4a9e8a9ecf9e189f659fb79f0ea069a0c9a02fa19aa10aa2" +
    "7fa2faa27ba301a48da41fa5b7a555a6f9a6a2a752a807a9c2a983aa4aab16ac" +
    "e8acc0ad9dae80af67b055b147b23eb33bb43cb542b64db75cb870b988baa5bb" +
    "c6bceabd13bf40c070c1a4c2dcc317c556c698c7ddc825ca71cbbfcc11ce65cf" +
    "bcd016d272d3d1d433d697d7fdd866dad1db3eddadde1ee092e107e37fe4f8e5" +
    "73e7f0e86feaefeb71edf5ee7af001f28af313f59ff62cf8baf949fbdafc6dfe" +
    "000095012b03c2045a06f4078e092a0bc60c640e0310a3114313e51488162b18" +
    "d019751b1b1dc21e6a201322bc2366251127bc28682a142cc12d6e2f1c31c932" +
    "76342336cf377b39243bcc3c703e1140ae414543d5445c46da474c49b24a0a4c" +
    "534d8d4eb74fd250dc51d852c553a55478553e56fa56ab575358f2588959195a" +
    "a25a245ba15b185c8a5cf85c615dc65d285e865ee15e385f8d5fe05f2f607d60" +
    "c860116158619d61e06122626262a062dd62196353638c63c463fb6330646564" +
    "9864cb64fc642d655d658c65ba65e765146640666b669666c066e96612673a67" +
    "61678867af67d567fa671f68436867688b68ae68d168f3681569376958697869" +
    "9969b969d969f869176a366a546a726a906aae6acb6ae86a056b216b3d6b596b" +
    "756b916bac6bc76be26bfc6b166c316c4a6c646c7e6c976cb06cc96ce26cfa6c" +
    "136d2b6d436d5b6d736d8a6da16db96dd06de76dfd6d146e2a6e416e576e6d6e" +
    "836e996eae6ec46ed96eef6e046f196f2e6f426f576f6c6f806f946fa96fbd6f" +
    "d16fe56ff86f0c702070337046705a706d7080709370a670b970cc70de70f170" +
    "0371167128713a714c715f71717182719471a671b871c971db71ec71fe710f72" +
    "20723172437254726572767286729772a872b972c972da72ea72fb720b731b73" +
    "2b733c734c735c736c737c738c739b73ab73bb73cb73da73ea73f97309741874" +
    "28743774467455746574747483749274a174b074bf74ce74dc74eb74fa740975" +
    "1775267534754375517560756e757d758b759975a775b675c475d275e075ee75" +
    "fc750a7618762676347641764f765d766b76787686769476a176af76bc76ca76" +
    "d776e576f276ff760d771a772777357742774f775c7769777677837790779d77" +
    "aa77b777c477d177de77eb77f877047811781e782b783778447851785d786a78" +
    "767883788f789c78a878b578c178cd78da78e678f278ff780b79177923793079" +
    "3c794879547960796c797879847990799c79a879b479c079cc79d879e479f079" +
    "fb79077a137a1f7a2b7a367a427a4e7a597a657a717a7c7a887a937a9f7aaa7a" +
    "b67ac17acd7ad87ae47aef7afb7a067b117b1d7b287b337b3f7b4a7b557b607b" +
    "6c7b777b827b8d7b987ba47baf7bba7bc57bd07bdb7be67bf17bfc7b077c127c" +
    "1d7c287c337c3e7c497c547c5f7c6a7c757c7f7c8a7c957ca07cab7cb57cc07c" +
    "cb7cd67ce07ceb7cf67c007d0b7d167d207d2b7d367d407d4b7d557d607d6a7d" +
    "757d807d8a7d957d9f7da97db47dbe7dc97dd37dde7de87df27dfd7d077e117e" +
    "1c7e267e307e3b7e457e4f7e5a7e647e6e7e787e837e8d7e977ea17eab7eb57e" +
    "c07eca7ed47ede7ee87ef27efc7e067f107f1b7f257f2f7f397f437f4d7f577f" +
    "617f6b7f757f7f7f887f927f9c7fa67fb07fba7fc47fce7fd87fe27feb7ff57f" +
    "ff7f"
)
# --- END TUBE_CURVE ---

# --- BEGIN TAPE_CURVE ---
TAPE_CURVE = bytes.fromhex(
    "018039807280aa80e3801c8154818d81c681fe8137827082a982e2821b835483" +
    "8d83c683ff8338847184aa84e4841d8556859085c98502863c867586af86e986" +
    "22875c879687cf87098843887d88b788f1882b8965899f89d989138a4d8a878a" +
    "c28afc8a368b718bab8be58b208c5a8c958ccf8c0a8d458d7f8dba8df58d308e" +
    "6b8ea58ee08e1b8f568f918fcc8f079043907e90b990f4902f916b91a691e291" +
    "1d9258929492cf920b9347938293be93fa9335947194ad94e994259561959d95" +
    "d995159651968d96c996059741977e97ba97f69732986f98ab98e89824996199" +
    "9d99da99169a539a909acd9a099b469b839bc09bfd9b3a9c779cb49cf19c2e9d" +
    "6b9da89de59d229e609e9d9eda9e179f559f929fd09f0da04ba088a0c6a003a1" +
    "41a17fa1bca1faa138a276a2b3a2f1a22fa36da3aba3e9a327a465a4a3a4e1a4" +
    "1fa55ea59ca5daa518a657a695a6d3a612a750a78ea7cda70ca84aa889a8c7a8" +
    "06a945a983a9c2a901aa40aa7eaabdaafcaa3bab7aabb9abf8ab37ac76acb5ac" +
    "f4ac33ad73adb2adf1ad30ae70aeafaeeeae2eaf6dafadafecaf2bb06bb0abb0" +
    "eab02ab169b1a9b1e9b129b268b2a8b2e8b228b368b3a7b3e7b327b467b4a7b4" +
    "e7b427b567b5a8b5e8b528b668b6a8b6e9b629b769b7a9b7eab72ab86bb8abb8" +
    "ebb82cb96cb9adb9eeb92eba6fbaafbaf0ba31bb71bbb2bbf3bb34bc74bcb5bc" +
    "f6bc37bd78bdb9bdfabd3bbe7cbebdbefebe3fbf80bfc1bf02c044c085c0c6c0" +
    "07c148c18ac1cbc10cc24ec28fc2d1c212c353c395c3d6c318c459c49bc4ddc4" +
    "1ec560c5a1c5e3c525c667c6a8c6eac62cc76ec7afc7f1c733c875c8b7c8f9c8" +
    "3bc97dc9bfc901ca43ca85cac7ca09cb4bcb8dcbcfcb12cc54cc96ccd8cc1acd" +
    "5dcd9fcde1cd24ce66cea8ceebce2dcf6fcfb2cff4cf37d079d0bcd0fed041d1" +
    "83d1c6d109d24bd28ed2d0d213d356d399d3dbd31ed461d4a3d4e6d429d56cd5" +
    "afd5f2d534d677d6bad6fdd640d783d7c6d709d84cd88fd8d2d815d958d99bd9" +
    "ded921da64daa7daebda2edb71dbb4dbf7db3adc7edcc1dc04dd47dd8bddcedd" +
    "11de55de98dedbde1fdf62dfa5dfe9df2ce06fe0b3e0f6e03ae17de1c1e104e2" +
    "48e28be2cfe212e356e399e3dde320e464e4a8e4ebe42fe572e5b6e5fae53de6" +
    "81e6c5e608e74ce790e7d4e717e85be89fe8e3e826e96ae9aee9f2e935ea79ea" +
    "bdea01eb45eb89ebcceb10ec54ec98ecdcec20ed64eda7edebed2fee73eeb7ee" +
    "fbee3fef83efc7ef0bf04ff093f0d7f01bf15ff1a3f1e7f12bf26ff2b3f2f7f2" +
    "3bf37ff3c3f307f44bf48ff4d3f417f55bf59ff5e3f527f66bf6b0f6f4f638f7" +
    "7cf7c0f704f848f88cf8d0f814f959f99df9e1f925fa69faadfaf1fa35fb7afb" +
    "befb02fc46fc8afccefc12fd57fd9bfddffd23fe67feabfeeffe34ff78ffbcff" +
    "000044008800cc00110155019901dd0121026502a902ee0232037603ba03fe03" +
    "42048604cb040f0553059705db051f066306a706ec0630077407b807fc074008" +
    "8408c8080c0950099509d9091d0a610aa50ae90a2d0b710bb50bf90b3d0c810c" +
    "c50c090d4d0d910dd50d190e5d0ea10ee50e290f6d0fb10ff50f39107d10c110" +
    "051149118d11d111151259129c12e01224136813ac13f01334147714bb14ff14" +
    "43158715cb150e1652169616da161d176117a517e9172c187018b418f8183b19" +
    "7f19c319061a4a1a8e1ad11a151b581b9c1be01b231c671caa1cee1c311d751d" +
    "b81dfc1d3f1e831ec61e0a1f4d1f911fd41f17205b209e20e12025216821ab21" +
    "ef2132227522b922fc223f238223c62309244c248f24d224152559259c25df25" +
    "22266526a826eb262e277127b427f7273a287d28c028032946298929cc290e2a" +
    "512a942ad72a1a2b5d2b9f2be22b252c672caa2ced2c302d722db52df72d3a2e" +
    "7d2ebf2e022f442f872fc92f0c304e309130d330153158319a31dc311f326132" +
    "a332e63228336a33ac33ee3331347334b534f73439357b35bd35ff3541368336" +
    "c536073749378b37cd370f3851389238d438163958399939db391d3a5f3aa03a" +
    "e23a233b653ba73be83b2a3c6b3cad3cee3c2f3d713db23df43d353e763eb83e" +
    "f93e3a3f7b3fbc3ffe3f3f408040c140024143418441c541064247428842c942" +
    "0a434b438c43cc430d444e448f44cf44104551459145d245124653469446d446" +
    "154755479547d647164857489748d748174958499849d849184a584a994ad94a" +
    "194b594b994bd94b194c594c984cd84c184d584d984dd74d174e574e974ed64e" +
    "164f554f954fd54f145053509350d250125151519051d0510f524e528d52cd52" +
    "0c534b538a53c953085447548654c554045543558255c055ff553e567d56bb56" +
    "fa5639577757b657f45733587258b058ee582d596b59a959e859265a645aa25a" +
    "e15a1f5b5d5b9b5bd95b175c555c935cd15c0f5d4d5d8a5dc85d065e445e815e" +
    "bf5efd5e3a5f785fb55ff35f30606e60ab60e96026616361a061de611b625862" +
    "9562d2620f634c638963c663036440647d64ba64f76433657065ad65ea652666" +
    "63669f66dc66186755679167ce670a6846688268bf68fb6837697369af69eb69" +
    "276a636a9f6adb6a176b536b8f6bcb6b066c426c7e6cb96cf56c316d6c6da86d" +
    "e36d1e6e5a6e956ed16e0c6f476f826fbd6ff96f34706f70aa70e57020715b71" +
    "9571d0710b7246728172bb72f67231736b73a673e0731b7455748f74ca740475" +
    "3e757975b375ed75277661769b76d5760f7749778377bd77f77731786a78a478" +
    "de78177951798b79c479fe79377a707aaa7ae37a1c7b567b8f7bc87b017c3a7c" +
    "737cac7ce57c1e7d577d907dc97d027e3a7e737eac7ee47e1d7f567f8e7fc77f" +
    "ff7f"
)
# --- END TAPE_CURVE ---

# --- BEGIN IRON_CURVE ---
IRON_CURVE = bytes.fromhex(
    "018039807280aa80e3801c8154818d81c681fe8137827082a982e2821b835483" +
    "8d83c683ff8338847184aa84e4841d8556859085c98502863c867586af86e986" +
    "22875c879687cf87098843887d88b788f1882b8965899f89d989138a4d8a878a" +
    "c28afc8a368b718bab8be58b208c5a8c958ccf8c0a8d458d7f8dba8df58d308e" +
    "6b8ea58ee08e1b8f568f918fcc8f079043907e90b990f4902f916b91a691e291" +
    "1d9258929492cf920b9347938293be93fa9335947194ad94e994259561959d95" +
    "d995159651968d96c996059741977e97ba97f69732986f98ab98e89824996199" +
    "9d99da99169a539a909acd9a099b469b839bc09bfd9b3a9c779cb49cf19c2e9d" +
    "6b9da89de59d229e609e9d9eda9e179f559f929fd09f0da04ba088a0c6a003a1" +
    "41a17fa1bca1faa138a276a2b3a2f1a22fa36da3aba3e9a327a465a4a3a4e1a4" +
    "1fa55ea59ca5daa518a657a695a6d3a612a750a78ea7cda70ca84aa889a8c7a8" +
    "06a945a983a9c2a901aa40aa7eaabdaafcaa3bab7aabb9abf8ab37ac76acb5ac" +
    "f4ac33ad73adb2adf1ad30ae70aeafaeeeae2eaf6dafadafecaf2bb06bb0abb0" +
    "eab02ab169b1a9b1e9b129b268b2a8b2e8b228b368b3a7b3e7b327b467b4a7b4" +
    "e7b427b567b5a8b5e8b528b668b6a8b6e9b629b769b7a9b7eab72ab86bb8abb8" +
    "ebb82cb96cb9adb9eeb92eba6fbaafbaf0ba31bb71bbb2bbf3bb34bc74bcb5bc" +
    "f6bc37bd78bdb9bdfabd3bbe7cbebdbefebe3fbf80bfc1bf02c044c085c0c6c0" +
    "07c148c18ac1cbc10cc24ec28fc2d1c212c353c395c3d6c318c459c49bc4ddc4" +
    "1ec560c5a1c5e3c525c667c6a8c6eac62cc76ec7afc7f1c733c875c8b7c8f9c8" +
    "3bc97dc9bfc901ca43ca85cac7ca09cb4bcb8dcbcfcb12cc54cc96ccd8cc1acd" +
    "5dcd9fcde1cd24ce66cea8ceebce2dcf6fcfb2cff4cf37d079d0bcd0fed041d1" +
    "83d1c6d109d24bd28ed2d0d213d356d399d3dbd31ed461d4a3d4e6d429d56cd5" +
    "afd5f2d534d677d6bad6fdd640d783d7c6d709d84cd88fd8d2d815d958d99bd9" +
    "ded921da64daa7daebda2edb71dbb4dbf7db3adc7edcc1dc04dd47dd8bddcedd" +
    "11de55de98dedbde1fdf62dfa5dfe9df2ce06fe0b3e0f6e03ae17de1c1e104e2" +
    "48e28be2cfe212e356e399e3dde320e464e4a8e4ebe42fe572e5b6e5fae53de6" +
    "81e6c5e608e74ce790e7d4e717e85be89fe8e3e826e96ae9aee9f2e935ea79ea" +
    "bdea01eb45eb89ebcceb10ec54ec98ecdcec20ed64eda7edebed2fee73eeb7ee" +
    "fbee3fef83efc7ef0bf04ff093f0d7f01bf15ff1a3f1e7f12bf26ff2b3f2f7f2" +
    "3bf37ff3c3f307f44bf48ff4d3f417f55bf59ff5e3f527f66bf6b0f6f4f638f7" +
    "7cf7c0f704f848f88cf8d0f814f959f99df9e1f925fa69faadfaf1fa35fb7afb" +
    "befb02fc46fc8afccefc12fd57fd9bfddffd23fe67feabfeeffe34ff78ffbcff" +
    "000044008800cc00110155019901dd0121026502a902ee0232037603ba03fe03" +
    "42048604cb040f0553059705db051f066306a706ec0630077407b807fc074008" +
    "8408c8080c0950099509d9091d0a610aa50ae90a2d0b710bb50bf90b3d0c810c" +
    "c50c090d4d0d910dd50d190e5d0ea10ee50e290f6d0fb10ff50f39107d10c110" +
    "051149118d11d111151259129c12e01224136813ac13f01334147714bb14ff14" +
    "43158715cb150e1652169616da161d176117a517e9172c187018b418f8183b19" +
    "7f19c319061a4a1a8e1ad11a151b581b9c1be01b231c671caa1cee1c311d751d" +
    "b81dfc1d3f1e831ec61e0a1f4d1f911fd41f17205b209e20e12025216821ab21" +
    "ef2132227522b922fc223f238223c62309244c248f24d224152559259c25df25" +
    "22266526a826eb262e277127b427f7273a287d28c028032946298929cc290e2a" +
    "512a942ad72a1a2b5d2b9f2be22b252c672caa2ced2c302d722db52df72d3a2e" +
    "7d2ebf2e022f442f872fc92f0c304e309130d330153158319a31dc311f326132" +
    "a332e63228336a33ac33ee3331347334b534f73439357b35bd35ff3541368336" +
    "c536073749378b37cd370f3851389238d438163958399939db391d3a5f3aa03a" +
    "e23a233b653ba73be83b2a3c6b3cad3cee3c2f3d713db23df43d353e763eb83e" +
    "f93e3a3f7b3fbc3ffe3f3f408040c140024143418441c541064247428842c942" +
    "0a434b438c43cc430d444e448f44cf44104551459145d245124653469446d446" +
    "154755479547d647164857489748d748174958499849d849184a584a994ad94a" +
    "194b594b994bd94b194c594c984cd84c184d584d984dd74d174e574e974ed64e" +
    "164f554f954fd54f145053509350d250125151519051d0510f524e528d52cd52" +
    "0c534b538a53c953085447548654c554045543558255c055ff553e567d56bb56" +
    "fa5639577757b657f45733587258b058ee582d596b59a959e859265a645aa25a" +
    "e15a1f5b5d5b9b5bd95b175c555c935cd15c0f5d4d5d8a5dc85d065e445e815e" +
    "bf5efd5e3a5f785fb55ff35f30606e60ab60e96026616361a061de611b625862" +
    "9562d2620f634c638963c663036440647d64ba64f76433657065ad65ea652666" +
    "63669f66dc66186755679167ce670a6846688268bf68fb6837697369af69eb69" +
    "276a636a9f6adb6a176b536b8f6bcb6b066c426c7e6cb96cf56c316d6c6da86d" +
    "e36d1e6e5a6e956ed16e0c6f476f826fbd6ff96f34706f70aa70e57020715b71" +
    "9571d0710b7246728172bb72f67231736b73a673e0731b7455748f74ca740475" +
    "3e757975b375ed75277661769b76d5760f7749778377bd77f77731786a78a478" +
    "de78177951798b79c479fe79377a707aaa7ae37a1c7b567b8f7bc87b017c3a7c" +
    "737cac7ce57c1e7d577d907dc97d027e3a7e737eac7ee47e1d7f567f8e7fc77f" +
    "ff7f"
)
# --- END IRON_CURVE ---

CHARACTERS = ("tube", "tape", "console")
OVERSAMPLES = (1, 2, 4, 8)
LEAN_PATCH = 8
#: One factor below whatever the rate ships: see `_build`.
#: The rate picks the factor, on measurement rather than on habit. At
#: maximum Drive with a 3700 Hz probe the alias floor reads, per factor:
#: 48 kHz x1 -35.977, x2 -57.200, **x4 -63.847**, x8 -64.770 — x4 is the
#: first factor that clears the -60 bar and x8 buys 0.923 dB for another
#: 1.408 ms of S3 block. 44.1 kHz x2 -47.034, x4 -47.763, x8 -47.735 —
#: nothing clears, because h6 of 3700 Hz is above that rate's Nyquist and
#: folds back whatever the internal rate was. 22.05 kHz x2 -17.590,
#: x4 -17.609, x8 -17.613 — 0.023 dB apart, so the class takes the
#: cheapest factor that is not x1 (which is 4.3 dB worse there, and
#: 4.078 dB worse at the default).
OVERSAMPLE_RATE_HZ = 32000.0
#: `audioshaper.Waveshaper` clamps its own output at int16 (`to_s16`), so a
#: `post_gain` that asks the node for more than full scale hard-clips at the
#: BASE rate, downstream of the decimator, where no oversampling factor can
#: reach it — Distortion's audioif#99, re-measured on this curve. The tube
#: table is smooth, so unlike a diode clipper it does not ring: the bare
#: node on this table at 1010 Hz, 0 dBFS, x8 reads -95.331 dB of inharmonic
#: energy at an output peak of 0.98120 and -70.233 at 1.00000, a 25 dB step
#: at the rail and nothing before it. So the ceiling here is the rail, not
#: Distortion's 0.74, and this is 0.16 dB under it.
NODE_CEILING = 0.98

#: The makeup stage the third fix round added, and the corner it shelves
#: at. What the node gives up at `NODE_CEILING` used to go onto the wet
#: mixer voice as `level > 1.0` - and **a mixer voice clamps at 1.0**, so
#: Output +6 delivered +5.965 dB and Output +12 delivered **+7.866**
#: (1 kHz, -12 dBFS). The test that should have caught it multiplied
#: `post_gain` by the level in Python and never rendered (audit 3 (p)1,
#: ruling (o)). A `HIGH_SHELF` at 10 Hz is a flat boost everywhere a note
#: lives - 0.02 dB down at 100 Hz - and it is the one node in the palette
#: that can carry a gain above unity behind the shaper.
MAKEUP_SHELF_HZ = 10.0

#: The output mixer's buffer, per channel. `Mixer._render_size` is
#: `buffer_size // 2 // 4 * 4` BYTES, so the 1024 this class shipped handed
#: back **128 stereo frames** and every node behind it — the `Splitter`,
#: whose own chunk is 256 frames, the oversampled shaper and the three
#: biquads — was pulled TWICE per 256-frame block. 256 frames is the
#: palette's block and the unit every audioif node works in, and
#: `1024 * channel_count` is one pull per block at either channel count.
#: `Distortion` already does this (`_pcm_mixer`) and came in inside its
#: budget on both boards; `Saturation`, `Exciter` and `Bitcrusher` were the
#: three that did not. Measured on the sub-graph alone, six alternating
#: reps in one process on desktop MicroPython: **0.0736 ms/block at 128
#: frames against 0.0672 at 256**, 8.7 % of what the sub-graph costs.
MIXER_BUFFER_BYTES = 1024

#: How many blocks `_charge_coupling` pulls, and how long the zero sample
#: it pulls through is. The plate coupling pole is 6.8 Hz, so its charge is
#: about 0.23 s; 32 blocks of 512 frames is 16 384 and covers it at every
#: rate. The shaper's native `play()` takes no `loop`, so the sample is a
#: block long and is re-played each pull.
CHARGE_BLOCKS = 32
CHARGE_FRAMES = 512
TILT_HZ = 1000.0
PLATE_HZ = 20.0
# 20 Hz, not the 5 Hz this was while it sat at the grid. The node's kernel
# is Q15 (audioif#77), and a 5 Hz pole at 48 kHz sits at radius 0.99935,
# where a biquad's rounding noise gain is enormous. In front of the shaper
# that noise was attenuated by `pre_gain`; at the plate it lands on the
# output, and A4 read 12 dB worse for it (1010 Hz Drive 0: -65.8 against
# -78.4 at 20 Hz). 20 Hz is an ordinary plate-coupling corner and it costs
# nothing the class is for.
FLUX_HZ = 5.0
LOSS_HZ_AT_15 = 10700.0
SPEED_REF = 15.0
BUTTER_Q = 0.7071067811865475

# Drive 0 dB, 0 dBFS = 1 V jack. Tube table x=+-1 is +-10 V grid.
# post_gain stays 1 at Drive 0 so the plate ceiling still fits in Q15
# (unity through 36 dB of triode gain would clip TU1's -6 dBFS probe).
TUBE_PRE0 = 0.1
# The table is normalised to its own grid-conduction extreme so it fills
# Q15 (generator, audiocomponents#76); this carries that 1.6049 back out,
# so the class's level is where it was.
TUBE_MAKEUP = 0.623086
# Tape table x=+-1 is H/a=+-1; 0 dBFS -> H/a=0.2.
TAPE_PRE0 = 0.2
TAPE_MAKEUP = 1.0
# Iron: 5 Hz one-pole is ~-26 dB at 100 Hz (100/5); same Langevin.
IRON_PRE0 = 4.0
IRON_MAKEUP = 1.0

#: Drive's ceiling, and now the ceiling on everything in front of the
#: curve. Headroom moves the character's knee and Drive moves the signal
#: at it, and on this palette those are one number — the node has one gain
#: before the table — so `pre = pre0 * drive / head` made Headroom a second
#: Drive with +27 dB of reach behind a documented +15 dB cap, and A4 failed
#: from the shipped surface at Headroom -6 / Output +6 (-45.621 at 3700 Hz,
#: audiocomponents#70). The cap is on the pair.
DRIVE_CEILING_DB = 15.0

_RANGES = (
    (-12.0, 15.0),         # 0 Drive, dB - A4's ceiling, not a taste call
    (-24.0, 12.0),         # 1 Output, dB
    (0.0, 1.0),            # 2 Mix
    (-12.0, 12.0),         # 3 Headroom, dB
    (-1.0, 1.0),           # 4 Bias
    (3.75, 30.0, "log"),   # 5 Speed, ips
    (-6.0, 6.0),           # 6 Tilt, dB
    (0.0, 1.0),            # 7 Hysteresis
)

_GROUP_DELAY_SAMPLES = {1: 0.0, 2: 2.2, 4: 3.3, 8: 3.9}
#: `console`'s two `audioecho.FeedbackDelay` sections, one sample of pure
#: delay each. **It is 2 and not the 9.5 a sub-sample CLICK reads**, and
#: the difference is worth the sentence: the 5 Hz damping and cut filters
#: inside those sections have group delay, and `kit.click`'s own docstring
#: says group delay "is a real property of the class and *not* the
#: processing latency `latency_samples` declares". Read as the integer
#: onset - `subsample=False`, which is the reading this row wants - a
#: click comes out where 2 says it will. Read sub-sample it is **12.774**
#: at 48 kHz on an impulse and **16.808** on a 4 ms burst, because the
#: envelope of a 5 Hz-filtered click is probe-dependent. Both readings are
#: in the pack; only one of them is a latency.
CONSOLE_EXTRA_SAMPLES = 2.0


#: Each macro's public mode, in index order, written out beside `_RANGES`
#: because `macro_of` needs it: a BIPOLAR macro's MIDI law has a centre
#: detent at 64 and a UNIPOLAR one does not (audiocomponents#87), so a patch
#: authored without the mode lands beside its engineering value. It is the
#: same list as `MACRO_MODES` below, which stays written out as a literal
#: for the hosts that read it out of the source; the shared contract test
#: holds the two in step.
_MODES = ("UNIPOLAR", "UNIPOLAR", "UNIPOLAR", "UNIPOLAR",
          "BIPOLAR", "UNIPOLAR", "BIPOLAR", "UNIPOLAR")


def _patch(*engineering):
    return tuple(_component.macro_of(span, value, mode)
                 for span, mode, value in zip(_RANGES, _MODES, engineering))


def _q15_array(blob):
    out = array("h")
    frombytes = getattr(out, "frombytes", None)
    if frombytes is not None:
        frombytes(blob)
        return out
    for index in range(0, len(blob), 2):
        value = blob[index] | (blob[index + 1] << 8)
        if value >= 32768:
            value -= 65536
        out.append(value)
    return out


#: What a click actually reads, per character and oversampling factor -
#: **measured, not derived**, by the third fix round.
#:
#: There were two readings and one declaration. `_GROUP_DELAY_SAMPLES` is
#: the half-band's group delay, which is where a symmetric response's
#: *centroid* sits; the onset of that response arrives **before** its
#: centroid, and an onset detector answers the onset. So `tube` graded
#: sub-sample and failed the integer onset by 2 samples, `console` graded
#: integer and failed sub-sample, and **10 of 18 build x rate cells were
#: red** on one reading or the other (audit 3 (p)8, G7).
#:
#: This class declares the **integer onset**, which is the reading a host
#: doing sample-accurate delay compensation can use and the one
#: `Distortion` already declares (`CLICK_DELAY_SAMPLES` there). The
#: sub-sample group delay is a real property of the graph and is named in
#: the docstring; it is not what `latency_samples` reports.
#: Measured at 48 kHz with an impulse at frame 400, stereo and mono; the
#: same factor reads within the kit's 1-sample bar at 44.1 and 22.05 kHz,
#: which is the whole of what a declaration can promise about an onset the
#: filters move by a fraction of a sample.
CLICK_ONSET_SAMPLES = {
    ("tube", 1): 0, ("tube", 2): 0, ("tube", 4): 1, ("tube", 8): 2,
    ("tape", 1): 0, ("tape", 2): 1, ("tape", 4): 2, ("tape", 8): 2,
    ("console", 1): 2, ("console", 2): 3, ("console", 4): 4,
    ("console", 8): 5,
}


def _group_delay_samples(oversample, extra=0.0):
    """Rounded once, at the end. Rounding the two terms separately is how
    `console` came to declare 2 samples for 9.46."""
    return int(round(_GROUP_DELAY_SAMPLES[int(oversample)] + extra))


def _click_onset_samples(character, oversample):
    """The declaration: what an onset detector reads at this build."""
    return CLICK_ONSET_SAMPLES[(character, int(oversample))]


def shipped_oversample(sample_rate):
    """The factor this rate ships with: x4 at 48 and 44.1 kHz, x2 at 22.05.

    Taken from the alias floor at each factor rather than from a rule of
    thumb — the numbers are at `OVERSAMPLE_RATE_HZ`. Above x4 the floor at
    every supported rate is harmonic fold-back, which is the base rate's
    Nyquist and not the oversampler's business, so the factors above it are
    S3 block for nothing.
    """
    return 4 if float(sample_rate) >= OVERSAMPLE_RATE_HZ else 2


class Saturation(_component.Component):
    """A 12AX7 stage, a tape machine, or transformer iron."""

    NAME = 'Saturation'
    DISPLAY_NAME = 'Saturation'
    CATEGORIES = ('Distortion',)
    VERSION = '0.1.0'

    TIER = _component.AUDIOIF
    REQUIRES = ("audioshaper", "audiobiquad", "audioroute", "audioecho")

    CAPABILITIES = ()
    #: The shipped x4 group delay, 3.3 samples. The instance property is the
    #: one to read: Mix 0 is 0, the lean patch's x2 is 2, `console` adds 2.
    LATENCY_SAMPLES = 3
    #: Measured, not inherited. The longest memory in the graph is the 20 Hz
    #: plate capacitor - 5 Hz on `console`, which is the slow one. A 200 ms
    #: 0 dBFS burst's residual reaches 0 LSB **3282 frames** after the burst
    #: on `tube` at 48 kHz, 3196 on `tape` and **13759 on `console`** (0.287 s
    #: at every rate, since the corner is in hertz). 65536 is 1.365 s at
    #: 48 kHz, 4.8x the worst of those. The 655360 this used to declare was
    #: 13.65 s and was in neither the pack nor a measurement.
    TAIL_SAMPLES = 65536

    MACRO_LABELS = ("Drive", "Output", "Mix", "Headroom", "Bias", "Speed",
                    "Tilt", "Hysteresis")
    MACRO_MODES = {
        0: "UNIPOLAR", 1: "UNIPOLAR", 2: "UNIPOLAR", 3: "UNIPOLAR",
        4: "BIPOLAR", 5: "UNIPOLAR", 6: "BIPOLAR", 7: "UNIPOLAR",
    }
    _MACRO_RANGES = _RANGES
    PATCHES = {
        0: ("Gentle thickening",
            _patch(0.0, 0.0, 1.0, 0.0, 0.0, 15.0, 0.0, 0.0)),
        1: ("Hot into the curve",
            _patch(15.0, -6.0, 1.0, 0.0, 0.0, 15.0, 0.0, 0.0)),
        2: ("Tape at fifteen",
            _patch(6.0, 0.0, 1.0, 0.0, 0.0, 15.0, 0.0, 0.0)),
        3: ("Tape at seven and a half",
            _patch(6.0, 0.0, 1.0, 0.0, 0.0, 7.5, 0.0, 0.0)),
        4: ("Under-biased and bright",
            _patch(6.0, 0.0, 1.0, 0.0, -0.1, 15.0, 3.0, 0.0)),
        5: ("Iron, low end working",
            _patch(0.0, 0.0, 1.0, -6.0, 0.0, 15.0, 0.0, 0.0)),
        6: ("Offset, even harmonics",
            _patch(6.0, 0.0, 1.0, 0.0, 0.1, 15.0, 0.0, 0.0)),
        7: ("Mix back",
            _patch(6.0, 0.0, 0.35, 0.0, 0.0, 15.0, 0.0, 0.0)),
        LEAN_PATCH: ("Saturation - lean",
                     _patch(0.0, 0.0, 1.0, 0.0, 0.0, 15.0, 0.0, 0.0)),
    }

    def _build(self, drive_db=0.0, output_db=0.0, mix=1.0, headroom_db=0.0,
               bias=0.0, speed_ips=15.0, tilt_db=0.0, hysteresis=0.0,
               character="tube", oversample=None, patch=None):
        rate = self._sample_rate
        channels = self._channel_count
        if character not in CHARACTERS:
            raise ValueError(
                "character must be 'tube', 'tape' or 'console'")
        if oversample is None:
            oversample = shipped_oversample(rate)
        oversample = int(oversample)
        if oversample not in OVERSAMPLES:
            raise ValueError("oversample must be 1, 2, 4 or 8")
        self._character = character
        self._oversample = oversample
        # The lean patch is one factor down from whatever this rate ships,
        # so it stays a real escape valve at every rate instead of quietly
        # becoming patch 0 again the day the shipped factor moved to x4.
        self._lean_oversample = max(1, oversample // 2)
        self._extra_delay = (CONSOLE_EXTRA_SAMPLES
                             if character == "console" else 0.0)
        self._routed_lean = False
        self._ready = False
        self._attached = False
        self._bias = 0.0
        self._wet_head = 1.0
        self._group_delay = _group_delay_samples(oversample,
                                                 self._extra_delay)
        self._wet_delay = _click_onset_samples(character, oversample)
        self._latency = self._wet_delay if mix > 0.0 else 0

        self._split = self._own(
            audioroute.Splitter(source=self._source, taps=2), reset=False)
        dry = self._own(self._split.tap(0), reset=False)
        wet_in = self._own(self._split.tap(1), reset=False)

        if character == "tube":
            blob = TUBE_CURVE
        elif character == "tape":
            blob = TAPE_CURVE
        else:
            blob = IRON_CURVE
        curve_h = _q15_array(blob)
        self._curve = curve_h

        head = wet_in
        self._couple = None
        self._loss = None
        self._flux_lp = None
        self._flux_hp = None
        sample_ms = 1000.0 / float(rate)

        if character == "console":
            self._flux_lp = self._own(audioecho.FeedbackDelay(
                sample_rate=rate, channel_count=channels, max_delay_ms=5.0,
                delay_ms=sample_ms, feedback=0.0, mix=2.0,
                damping_hz=FLUX_HZ, cut_hz=0.0), reset=True)
            self._flux_lp.play(head)
            head = self._flux_lp

        self._shaper = self._own(audioshaper.Waveshaper(
            sample_rate=rate, channel_count=channels,
            curve=curve_h, oversample=oversample,
            pre_gain=1.0, post_gain=1.0, mix=1.0, bias=0.0,
            hysteresis=0.0))
        # Wired to the zero sample until `_charge_coupling` has run: the
        # plate's coupling pole is behind the shaper and starts cold, so a
        # Bias off centre banged its whole offset out of the first block -
        # 8 489 LSB at shipped patch 4 (audit 3 (p)6, ruling (n)).
        # Re-pointing it at `head` afterwards is the one `play()` the
        # caller was always paying for; doing it the other way round reads
        # the split's wet tap twice and leaves the dry one a block behind.
        self._quiet = self._own(audiocore.RawSample(
            array("h", bytes(2 * CHARGE_FRAMES * channels)),
            sample_rate=rate, channel_count=channels), reset=False)
        self._shaper_head = head
        self._shaper.play(self._quiet)
        # The lean patch's shaper. `oversample` is a construction key the
        # node will not take from `set()`, so the only way a patch can
        # change the factor is to own a second node and re-route to it.
        # Nothing pulls this one until patch 8 does, and a node nobody
        # pulls costs nothing per block.
        self._lean = None
        if self._lean_oversample < oversample:
            self._lean = self._own(audioshaper.Waveshaper(
                sample_rate=rate, channel_count=channels,
                curve=curve_h, oversample=self._lean_oversample,
                pre_gain=1.0, post_gain=1.0, mix=1.0, bias=0.0,
                hysteresis=0.0))
            self._lean.play(self._quiet)
        head = self._shaper

        if character == "console":
            self._flux_hp = self._own(audioecho.FeedbackDelay(
                sample_rate=rate, channel_count=channels, max_delay_ms=5.0,
                delay_ms=sample_ms, feedback=0.0, mix=2.0,
                damping_hz=0.0, cut_hz=FLUX_HZ), reset=True)
            self._after = self._flux_hp
            head = self._flux_hp
        else:
            # The coupling capacitor is at the plate, not at the grid.
            # With it in front of the shaper the Bias macro put its whole
            # operating-point shift on the output as DC: at Bias +-0.25 the
            # render was 0.49 of full scale of DC with the audio gone, and
            # patch 4's -0.4 was DC and nothing else. `console` never had
            # it, because its flux high-pass is already downstream. A tape
            # machine's playback head cannot reproduce DC either, so `tape`
            # gets one too, at the cost of a third biquad. The stage is now
            # direct-coupled at the input: DC on the source shifts the
            # operating point, as it would in a directly coupled stage.
            self._couple = self._own(audiobiquad.Biquad(
                mode=audiobiquad.HIGH_PASS, frequency=self._hz(PLATE_HZ),
                Q=BUTTER_Q, sample_rate=rate, channel_count=channels))
            self._after = self._couple
            head = self._couple

        if character == "tape":
            self._loss = self._own(audiobiquad.Biquad(
                mode=audiobiquad.LOW_PASS, frequency=self._hz(LOSS_HZ_AT_15),
                Q=BUTTER_Q, sample_rate=rate, channel_count=channels))
            self._loss.play(head)
            head = self._loss

        self._tilt = self._own(audiobiquad.Biquad(
            mode=audiobiquad.HIGH_SHELF, frequency=self._hz(TILT_HZ),
            Q=BUTTER_Q, gain_db=0.0, sample_rate=rate,
            channel_count=channels))
        self._tilt.play(head)
        # The makeup stage. It carries whatever the node gave up at
        # `NODE_CEILING`, which a mixer voice cannot.
        self._makeup_shelf = self._own(audiobiquad.Biquad(
            mode=audiobiquad.HIGH_SHELF,
            frequency=self._hz(MAKEUP_SHELF_HZ),
            Q=BUTTER_Q, gain_db=0.0, sample_rate=rate,
            channel_count=channels))
        self._makeup_shelf.play(self._tilt)
        self._after.play(self._shaper)
        self._mix = self._own(
            audiomixer.Mixer(voice_count=2,
                             **self._pcm(MIXER_BUFFER_BYTES * channels)),
            reset=self._reset_mixers)
        self._output = self._mix
        # Two frames, not one: `audiocore.get_buffer` of a 1-channel Mixer
        # whose voices loop a one-frame all-zero RawSample never returns on
        # MicroPython or CircuitPython (audioif#85). Two frames is the cure
        # `Fuzz`, `Overdrive`, `Distortion` and `Exciter` all take, and it
        # keeps one priming path for every interpreter and channel count.
        self._silence = self._own(audiocore.RawSample(
            array("h", bytes(2 * 2 * channels)),
            sample_rate=rate, channel_count=channels), reset=False)
        self._dry = dry

        # Macros write both mixer levels before any voice takes a source,
        # then the gates open at those levels (audiocomponents#66).
        self._init_macros(
            (drive_db, output_db, mix, headroom_db, bias, speed_ips,
             tilt_db, hysteresis),
            patch)
        self._charge_coupling()
        for shaper in self._shapers():
            shaper.play(self._shaper_head)
        _component.open_level_gates(
            self._mix, [self._mix.voice[0], self._mix.voice[1]],
            self._silence)
        self._ready = True
        self._refresh_output()

    def _charge_coupling(self, rewire=False):
        """Settle the plate coupling pole on the bias before block one.

        `Bias` is an offset into an asymmetric curve, so the shaper answers
        a silent input with a constant, and the pole behind it blocks the
        constant but not the step that starts it: shipped patches 4 and 6
        put **8 489 and 7 044 LSB** out of digital silence and settled to
        +-1 LSB over about 0.2 s (audit 3 (p)6). This pulls the offset
        through the pole with the shapers fed the class's own zero sample -
        **the split is not pulled and no source frame is consumed** - and
        stops as soon as a whole block comes back zero.

        A **live** Bias move - a `program_change` onto silence, most of
        all - re-charges with `rewire=True`. That costs one block: the
        re-point takes a block from the wet tap, so the dry tap is pulled
        once to match it, and the split stays level. Without it a change
        onto patch 4 banged 8 489 LSB out of nothing.

        On a build with no `audiocore.get_buffer` this does nothing and the
        bang is back.
        """
        pull = getattr(audiocore, "get_buffer", None)
        if pull is None or self._after is None:
            return False
        if not self._bias:
            if rewire:
                for shaper in self._shapers():
                    shaper.play(self._quiet)
                    shaper.play(self._shaper_head)
                pull(self._dry)
            return False
        for index in range(CHARGE_BLOCKS):
            for shaper in self._shapers():
                shaper.play(self._quiet)
            _state, data = pull(self._makeup_shelf)
            if not data:
                break
            # The first block back is what the pole held before the
            # shapers were re-pointed, so it says nothing about this bias.
            if index and not any(array("h", bytes(data))):
                break
        if rewire:
            for shaper in self._shapers():
                shaper.play(self._shaper_head)
            # One block from the dry tap, so the split stays level: the
            # re-point above took one from the wet one.
            pull(self._dry)
        return True

    def _attach(self):
        """Hand the mixer its real sources, once and not before they are
        wanted.

        `MixerVoice.play()` primes itself by pulling a block, so doing this
        at construction takes a block of the borrowed source and leaves it
        inside the Splitter — which nobody would notice while the output ran
        through the mixer, and which costs Mix 0 the first 5.3 ms of the
        material now that it hands the source back. Deferred to the first
        moment Mix leaves 0, the same block is the one the mixer goes on to
        serve.
        """
        if self._attached:
            return
        self._attached = True
        self._mix.voice[0].play(self._dry)
        self._mix.voice[1].play(self._makeup_shelf)

    def _reset_mixers(self):
        audiocore.reset_buffer(self._mix)
        if self._attached:
            self._mix.voice[0].play(self._dry)
            self._mix.voice[1].play(self._makeup_shelf)

    def _value(self, index):
        return _component.macro_value(self._MACRO_RANGES[index],
                                      self._macros[index])

    def _pre0(self):
        if self._character == "tube":
            return TUBE_PRE0
        if self._character == "tape":
            return TAPE_PRE0
        return IRON_PRE0

    def _makeup(self):
        if self._character == "tube":
            return TUBE_MAKEUP
        if self._character == "tape":
            return TAPE_MAKEUP
        return IRON_MAKEUP

    def _shapers(self):
        """Both waveshapers, so a patch change cannot land on a node that
        missed a knob."""
        if self._lean is None:
            return (self._shaper,)
        return (self._shaper, self._lean)

    def _apply_macro(self, index, position):
        value = _component.macro_value(self._MACRO_RANGES[index], position)
        if index in (0, 1, 3):
            self._push_gains()
        elif index == 2:
            self._push_mix()
            self._refresh_output()
        elif index == 4:
            self._bias = value
            for shaper in self._shapers():
                shaper.set(bias=value)
            self._push_gains()
            if self._ready:
                self._charge_coupling(rewire=True)
        elif index == 5:
            if self._loss is not None:
                # Whole hertz, and the shelf below in eighths of a dB:
                # a setting derived in Python float is computed in single
                # precision on a board and double on a desktop, so the two
                # run different filters before a sample is rendered
                # (audiocomponents#75). A coarse grid both formats hold
                # exactly is what survives the crossing.
                hz = round(LOSS_HZ_AT_15 * value / SPEED_REF)
                self._loss.frequency = self._hz(float(hz))
        elif index == 6:
            self._tilt.gain_db = round(value * 8.0) / 8.0
        elif index == 7:
            for shaper in self._shapers():
                shaper.set(hysteresis=value)

    def _curve_at(self, x):
        """The table at `x`, interpolated the way the node interpolates."""
        table = self._curve
        last = len(table) - 1
        if x <= -1.0:
            return float(table[0])
        if x >= 1.0:
            return float(table[last])
        position = (x + 1.0) * 0.5 * last
        index = int(position)
        if index >= last:
            return float(table[last])
        step = table[index + 1] - table[index]
        return table[index] + step * (position - index)

    def _reach(self, pre):
        """How much of full scale the node's own output takes, before
        `post_gain`, for a full-scale input at this `pre_gain`.

        All three tables are monotone — the generator's `--check` prints the
        step histogram, and the tube's 667 falling steps and 357 flat ones
        never turn — so the extremes of the window the input sweeps are the
        window's two ends. Two interpolated lookups per gain write, not a
        sweep, which is what a board can afford in `_apply_macro`.
        """
        bias = self._bias
        lo = self._curve_at(bias - pre)
        hi = self._curve_at(bias + pre)
        if lo < 0.0:
            lo = -lo
        if hi < 0.0:
            hi = -hi
        return (lo if lo > hi else hi) / 32768.0

    def _push_gains(self):
        """Drive and Headroom are one gain, and it stops at the same place.

        `Headroom` moves the character's knee and `Drive` moves the signal
        at it; in front of one curve on one node that is a single number,
        `drive / head`. Leaving them independent gave the pair +27 dB of
        reach behind a +15 dB cap and A4 failed at Headroom -6 / Output +6
        (audiocomponents#70). Turning Headroom down now buys the same dB
        Drive buys, and stops where Drive stops.

        The output level is then split between the node and the wet mixer
        voice so the node's own output stays under `NODE_CEILING`: past the
        rail it hard-clips at the base rate, behind the decimator, which is
        the one kind of alias no oversampling factor reaches (audioif#99).
        Twelve of this class's 75 shipped positions asked past it, all of
        them Output >= +6 dB, worst 1.618 at Headroom +6 / Output +12. The
        voice takes what the node gives up, so the level law is unchanged
        to the bit; a position that was already under the ceiling keeps
        exactly the split it had and its bytes do not move.
        """
        drive = _component.db_to_gain(self._value(0))
        output = _component.db_to_gain(self._value(1))
        head = _component.db_to_gain(self._value(3))
        ceiling = _component.db_to_gain(DRIVE_CEILING_DB)
        gain = drive / head
        if gain > ceiling:
            gain = ceiling
        pre = self._pre0() * gain
        post = self._makeup() * output / gain
        ask = post * self._reach(pre)
        if ask > NODE_CEILING:
            move = NODE_CEILING / ask
            self._wet_head = 1.0 / move
            post = post * move
        else:
            self._wet_head = 1.0
        for shaper in self._shapers():
            shaper.set(pre_gain=pre, post_gain=post)
        self._push_mix()

    def _push_mix(self):
        """The wet level, and the makeup the node gave up.

        `self._wet_head` is at least 1.0 and a mixer voice clamps at 1.0,
        so it goes on the makeup shelf and the voice carries Mix alone.
        Written in dB because that is what the node takes, and 0 dB when
        the split did not fire - which is 63 of this class's 75 shipped
        positions, whose bytes do not move.
        """
        mix = self._value(2)
        self._mix.voice[0].level = 1.0 - mix
        self._mix.voice[1].level = mix
        # Single precision: a board derives this in float32 and a desktop
        # in double, and it reaches a node (audiocomponents#75).
        self._makeup_shelf.gain_db = _f32(
            0.0 if self._wet_head <= 1.0
            else 20.0 * math.log10(self._wet_head))

    def _refresh_output(self):
        """Mix 0 is the borrowed source itself, not a path through the graph.

        A mixer voice at level 1.0 scales by 32768/32767, so every sample at
        or above 32736 comes back one LSB bigger, and since the pin moved to
        audioif `977ef26` the CPython twin reproduces that instead of hiding
        it (audioif#95). A wire routed through a mixer is therefore never
        bit-exact at full scale on any target. Handing back the source makes
        the invariant exact by construction — and free, since nothing in the
        graph is pulled at all while Mix is 0. `Fuzz` took the same cure.
        """
        if not self._ready:
            return
        if self._value(2) <= 0.0:
            self._output = self._source
            self._latency = 0
        else:
            self._attach()
            self._output = self._mix
            self._latency = self._wet_delay

    def program_change(self, index, channel=0, note_id=-1,
                       sample_position=0):
        _component.Component.program_change(self, index, channel, note_id,
                                            sample_position)
        self._route()
        self._refresh_output()

    def _route(self):
        """Patch 8 `Saturation - lean` is the only pull chain that shapes
        at x4 instead of x8. Nothing else in the graph moves, and the
        factor it drops is the one number the S3's budget turns on."""
        lean = self._patch_index == LEAN_PATCH and self._lean is not None
        if lean == self._routed_lean:
            return
        shaper = self._lean if lean else self._shaper
        factor = self._lean_oversample if lean else self._oversample
        self._after.play(shaper)
        self._routed_lean = lean
        self._wet_delay = _group_delay_samples(factor, self._extra_delay)
        self._refresh_output()

    @property
    def latency_samples(self):
        self._check_live()
        return int(self._latency)
