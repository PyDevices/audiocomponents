"""What is red in the lifecycle matrix today, class by class: the rows
`tests/test_lifecycle_matrix.py` holds as KNOWN_RED.

Counted on the quick matrix on CPython at audiodsp v0.6.6rc8, every class
the package serves. A row is (class NAME, event prefix, property) ->
(red cells in the quick matrix, their digest, the same for the full
matrix or None where it was not counted, reason). Each reason names the
issue that tracks it, or the docstring sentence that states it.
"""

R_JUMP = (
    "a control that jumps hands its node the new value at once, so the"
    " output steps; disclosed in docs/control-smoothing.md, lifted when"
    " the node ramps land (audiocomponents#153)")
R_THUMP = (
    "a Frequency jump to the bottom in one call rings the filter's kept"
    " state at full scale for about 30 ms, and the jump back buzzes between"
    " the rails (audiocomponents#162; the corner ramp of #153 fixes it)")
R_JUMP_THUMP = (
    R_JUMP[:-1] + "; a patch change that drops the corner far also"
    " thumps as #162 says)")
R_PHASE = (
    "a free-running phase (an LFO, a carrier, a sample-and-hold count)"
    " restarted by a reset or moved by a rate or patch change never meets"
    " the uninterrupted control again; the sound is the same, shifted"
    " (audiocomponents#154)")
R_STATE = (
    "state that outlives tail_samples: a detector re-attacking after a"
    " reset or a rejoin, or a filter's or coupling pole's residue a few"
    " LSB past the declared tail (audiocomponents#155)")
R_FUZZ_LEAN = (
    "the lean shaper follows the patch, so macros moved back after a move"
    " to or from Fuzz - lean stay at that patch's oversampling; with the"
    " coupling residue of #155 elsewhere (audiocomponents#156, #155)")
R_FUZZ_WANDER = (
    "patch 2's Bias -0.85 leaves 6 to 9 LSB out of silence, inside the"
    " 16 LSB wander the class states (audiocomponents#156)")
R_LADDER_OSC = (
    "patch 2, Sustained Sine At Cutoff, self-oscillates on purpose: the"
    " class states it does not hold silence in, silence out there")
R_STATED_P1 = (
    "Listen (DynamicEQ) and Output (Exciter) are stated not to be a"
    " bypass at Mix 0 (audiocomponents#156)")
R_EXCITER_PART = (
    "a reset on 100-frame buffers runs 28 frames ahead of the control"
    " afterwards; with #155's float residue (audiocomponents#157)")
R_142 = (
    "at patch 6 and 22.05 kHz a rejoin off Mix 0 differs from a fresh"
    " instance a few frames in; the 48 kHz first-frames half of the finding"
    " closed when Overdrive began building lazily (audiocomponents#142)")
R_DIST_P7 = (
    "a move to patch 7 before the first pull, at 22.05 kHz stereo, stays"
    " 1 to 2 LSB off a fresh build from frame 10 on, about one frame in"
    " eight, and never settles: a rounding residue nobody hears"
    " (audiocomponents#161)")


#: (class NAME, event prefix, property) -> (quick cells, digest, full
#: cells, digest, reason). The full matrix was not counted here (None).
KNOWN_RED = {
    ('AutoPan', 'E1-reset@block', 'P4'): (18, 'a620da1c', None, None, R_PHASE),
    ('AutoPan', 'E1-reset@part', 'P4'): (18, 'a471a429', None, None, R_PHASE),
    ('AutoPan', 'E11-', 'P4'): (2, '56854f54', None, None, R_PHASE),
    ('AutoPan', 'E11-', 'P5'): (2, '087aa9fa', None, None, R_JUMP),
    ('AutoPan', 'E4-', 'P4'): (2, '68d7673d', None, None, R_PHASE),
    ('AutoPan', 'E4-', 'P5'): (14, '571e6892', None, None, R_JUMP),
    ('AutoPan', 'E6-', 'P4'): (18, 'ab6136b8', None, None, R_PHASE),
    ('AutoPan', 'E6-', 'P5'): (40, '4a1ecd5f', None, None, R_JUMP),
    ('BandPass', 'E11-', 'P5'): (12, '87dc8d6e', None, None, R_JUMP_THUMP),
    ('BandPass', 'E2-reset_buffer', 'P4'): (4, '26674fe7', None, None, R_STATE),
    ('BandPass', 'E4-', 'P5'): (16, 'fbf1bc33', None, None, R_JUMP),
    ('BandPass', 'E4-m0=', 'P5'): (8, '766f04c3', None, None, R_THUMP),
    ('BandPass', 'E5-mix0', 'P4'): (4, '3db4de60', None, None, R_STATE),
    ('BandPass', 'E5-mix0', 'P5'): (28, 'cde90b31', None, None, R_JUMP),
    ('BandPass', 'E6-', 'P4'): (16, '1ac93213', None, None, R_STATE),
    ('BandPass', 'E6-', 'P5'): (60, '0e15635a', None, None, R_JUMP_THUMP),
    ('BandPass', 'E9-', 'P4'): (20, '7c7d321c', None, None, R_STATE),
    ('BandPass', 'E9-', 'P5'): (140, '331bff40', None, None, R_JUMP),
    ('Bitcrusher', 'E1-reset@block', 'P4'): (16, '0c568ee1', None, None, R_PHASE),
    ('Bitcrusher', 'E1-reset@part', 'P4'): (32, '28fc347f', None, None, R_PHASE),
    ('Bitcrusher', 'E11-', 'P4'): (6, 'ddb49c52', None, None, R_PHASE),
    ('Bitcrusher', 'E11-', 'P5'): (8, 'b8cd0394', None, None, R_JUMP),
    ('Bitcrusher', 'E4-', 'P4'): (8, '00998826', None, None, R_PHASE),
    ('Bitcrusher', 'E4-', 'P5'): (13, '4c09238b', None, None, R_JUMP),
    ('Bitcrusher', 'E5-mix0', 'P4'): (22, 'cae3b03e', None, None, R_PHASE),
    ('Bitcrusher', 'E5-mix0', 'P5'): (4, '158bbe35', None, None, R_JUMP),
    ('Bitcrusher', 'E6-', 'P4'): (48, 'c98676ff', None, None, R_PHASE),
    ('Bitcrusher', 'E6-', 'P5'): (45, '4976f308', None, None, R_JUMP),
    ('Bitcrusher', 'E9-', 'P4'): (145, '2d77c1d5', None, None, R_PHASE),
    ('Bitcrusher', 'E9-', 'P5'): (90, 'beeb46d3', None, None, R_JUMP),
    ('CabinetSim', 'E1-reset@block', 'P4'): (32, 'd4049af3', None, None, R_STATE),
    ('CabinetSim', 'E1-reset@part', 'P4'): (32, '18d29744', None, None, R_STATE),
    ('CabinetSim', 'E11-', 'P4'): (11, '5cfd274d', None, None, R_STATE),
    ('CabinetSim', 'E11-', 'P5'): (4, 'ee6cde24', None, None, R_JUMP),
    ('CabinetSim', 'E4-', 'P4'): (18, 'ba9b584b', None, None, R_STATE),
    ('CabinetSim', 'E4-', 'P5'): (18, '623e3fe9', None, None, R_JUMP),
    ('CabinetSim', 'E5-mix0', 'P4'): (23, '237af205', None, None, R_STATE),
    ('CabinetSim', 'E5-mix0', 'P5'): (32, 'af8b4b35', None, None, R_JUMP),
    ('CabinetSim', 'E6-', 'P4'): (47, '37613cc8', None, None, R_STATE),
    ('CabinetSim', 'E6-', 'P5'): (54, 'db421f52', None, None, R_JUMP),
    ('CabinetSim', 'E9-', 'P4'): (115, 'bd72fb3d', None, None, R_STATE),
    ('CabinetSim', 'E9-', 'P5'): (160, 'd4d046ca', None, None, R_JUMP),
    ('Chorus', 'E1-reset@block', 'P4'): (32, '4a87c73b', None, None, R_PHASE),
    ('Chorus', 'E1-reset@part', 'P4'): (32, 'e74bb915', None, None, R_PHASE),
    ('Chorus', 'E11-', 'P4'): (16, 'f8ff4250', None, None, R_PHASE),
    ('Chorus', 'E11-', 'P5'): (8, '214d7ede', None, None, R_JUMP),
    ('Chorus', 'E2-reset_buffer', 'P4'): (32, '44a3e08c', None, None, R_PHASE),
    ('Chorus', 'E4-', 'P4'): (38, 'd2f35c85', None, None, R_PHASE),
    ('Chorus', 'E4-', 'P5'): (26, '5c8eedb2', None, None, R_JUMP),
    ('Chorus', 'E5-mix0', 'P4'): (32, '42f78641', None, None, R_PHASE),
    ('Chorus', 'E5-mix0', 'P5'): (32, '5b6fcae7', None, None, R_JUMP),
    ('Chorus', 'E6-', 'P4'): (76, 'fb5be030', None, None, R_PHASE),
    ('Chorus', 'E6-', 'P5'): (64, '531f4b89', None, None, R_JUMP),
    ('Chorus', 'E9-', 'P4'): (128, '99555806', None, None, R_PHASE),
    ('Chorus', 'E9-', 'P5'): (160, '52dbd13a', None, None, R_JUMP),
    ('CombFilter', 'E11-', 'P4'): (4, '311df2e2', None, None, R_STATE),
    ('CombFilter', 'E11-', 'P5'): (8, 'becbb467', None, None, R_JUMP),
    ('CombFilter', 'E2-reset_buffer', 'P4'): (2, 'e484c73e', None, None, R_STATE),
    ('CombFilter', 'E4-', 'P4'): (7, '0906d487', None, None, R_STATE),
    ('CombFilter', 'E4-', 'P5'): (28, '90fd3f33', None, None, R_JUMP),
    ('CombFilter', 'E5-mix0', 'P5'): (28, '183f1bf1', None, None, R_JUMP),
    ('CombFilter', 'E6-', 'P4'): (22, 'ce80804b', None, None, R_STATE),
    ('CombFilter', 'E6-', 'P5'): (58, '1b4f34b8', None, None, R_JUMP),
    ('CombFilter', 'E9-', 'P5'): (140, '0123c6b0', None, None, R_JUMP),
    ('Compressor', 'E1-reset@block', 'P4'): (64, '425ab558', None, None, R_STATE),
    ('Compressor', 'E1-reset@part', 'P4'): (64, '56933d4c', None, None, R_STATE),
    ('Compressor', 'E10-patch', 'P4'): (4, '00f31b8a', None, None, R_STATE),
    ('Compressor', 'E11-', 'P4'): (8, 'e6342cf4', None, None, R_STATE),
    ('Compressor', 'E11-', 'P5'): (8, 'e77977a7', None, None, R_JUMP),
    ('Compressor', 'E4-', 'P4'): (12, '8e419543', None, None, R_STATE),
    ('Compressor', 'E4-', 'P5'): (30, '8cf81483', None, None, R_JUMP),
    ('Compressor', 'E5-mix0', 'P4'): (60, '1606976a', None, None, R_STATE),
    ('Compressor', 'E5-mix0', 'P5'): (57, '87bcb9cf', None, None, R_JUMP),
    ('Compressor', 'E6-', 'P4'): (158, '8a381bc5', None, None, R_STATE),
    ('Compressor', 'E6-', 'P5'): (158, 'f381ffce', None, None, R_JUMP),
    ('Compressor', 'E9-', 'P4'): (314, '9d0fc034', None, None, R_STATE),
    ('Compressor', 'E9-', 'P5'): (292, 'eef8a082', None, None, R_JUMP),
    ('DeEsser', 'E11-', 'P4'): (2, '6486a19d', None, None, R_STATE),
    ('DeEsser', 'E4-', 'P4'): (8, 'e51a0a4b', None, None, R_STATE),
    ('DeEsser', 'E4-', 'P5'): (11, '1042cde7', None, None, R_JUMP),
    ('DeEsser', 'E6-', 'P4'): (13, '0b358487', None, None, R_STATE),
    ('DeEsser', 'E6-', 'P5'): (24, '69f6566d', None, None, R_JUMP),
    ('Distortion', 'E1-reset@block', 'P4'): (48, 'd84a1067', None, None, R_STATE),
    ('Distortion', 'E1-reset@part', 'P4'): (48, 'ce661657', None, None, R_STATE),
    ('Distortion', 'E10-mix0', 'P4'): (1, 'dc494f03', None, None, R_STATE),
    ('Distortion', 'E11-', 'P4'): (4, 'b2d5e10e', None, None, R_STATE),
    ('Distortion', 'E11-', 'P5'): (12, '5be4892b', None, None, R_JUMP),
    ('Distortion', 'E12-p7', 'P4'): (1, '6b0d9f7a', None, None, R_DIST_P7),
    ('Distortion', 'E12-p7', 'PF'): (1, 'cd437448', None, None, R_DIST_P7),
    ('Distortion', 'E4-', 'P4'): (8, '8fd46470', None, None, R_STATE),
    ('Distortion', 'E4-', 'P5'): (12, '30b1a8d2', None, None, R_JUMP),
    ('Distortion', 'E5-mix0', 'P4'): (44, '14ea31c6', None, None, R_STATE),
    ('Distortion', 'E5-mix0', 'P5'): (38, '8e927361', None, None, R_JUMP),
    ('Distortion', 'E6-', 'P4'): (46, '365ceaaa', None, None, R_STATE),
    ('Distortion', 'E6-', 'P5'): (80, '8394cff7', None, None, R_JUMP),
    ('Distortion', 'E9-', 'P4'): (236, 'f3a8ddc3', None, None, R_STATE),
    ('Distortion', 'E9-', 'P5'): (174, '91062d1d', None, None, R_JUMP),
    ('DynamicEQ', 'E1-reset@block', 'P4'): (28, '0b10ffa7', None, None, R_STATE),
    ('DynamicEQ', 'E1-reset@part', 'P4'): (28, '4e33bc13', None, None, R_STATE),
    ('DynamicEQ', 'E11-', 'P4'): (16, 'a0afa5a4', None, None, R_STATE),
    ('DynamicEQ', 'E11-', 'P5'): (5, '58eb6244', None, None, R_JUMP),
    ('DynamicEQ', 'E4-', 'P1'): (4, '65f0c3d8', None, None, R_STATED_P1),
    ('DynamicEQ', 'E4-', 'P4'): (36, 'd098085e', None, None, R_STATE),
    ('DynamicEQ', 'E4-', 'P5'): (7, '2a550f56', None, None, R_JUMP),
    ('DynamicEQ', 'E5-mix0', 'P4'): (26, 'e755b82b', None, None, R_STATE),
    ('DynamicEQ', 'E5-mix0', 'P5'): (4, '66b6249f', None, None, R_JUMP),
    ('DynamicEQ', 'E6-', 'P4'): (59, '0a15a424', None, None, R_STATE),
    ('DynamicEQ', 'E6-', 'P5'): (40, '68c3a280', None, None, R_JUMP),
    ('DynamicEQ', 'E9-', 'P4'): (104, 'eeee87de', None, None, R_STATE),
    ('DynamicEQ', 'E9-', 'P5'): (20, 'cd16412c', None, None, R_JUMP),
    ('Exciter', 'E1-reset@block', 'P4'): (32, '2ea00aec', None, None, R_STATE),
    ('Exciter', 'E1-reset@part', 'P4'): (32, '862fb9d8', None, None, R_EXCITER_PART),
    ('Exciter', 'E11-', 'P4'): (14, '43436585', None, None, R_STATE),
    ('Exciter', 'E11-', 'P5'): (6, '3899ebe1', None, None, R_JUMP),
    ('Exciter', 'E4-', 'P1'): (4, '99c82410', None, None, R_STATED_P1),
    ('Exciter', 'E4-', 'P4'): (22, '07ff321c', None, None, R_STATE),
    ('Exciter', 'E4-', 'P5'): (10, 'd574090f', None, None, R_JUMP),
    ('Exciter', 'E5-mix0', 'P4'): (32, '93dc7e80', None, None, R_STATE),
    ('Exciter', 'E5-mix0', 'P5'): (32, 'cc57a31b', None, None, R_JUMP),
    ('Exciter', 'E6-', 'P4'): (68, 'ae6fb523', None, None, R_STATE),
    ('Exciter', 'E6-', 'P5'): (20, '21ec24b9', None, None, R_JUMP),
    ('Exciter', 'E9-', 'P4'): (160, '4359c45d', None, None, R_STATE),
    ('Exciter', 'E9-', 'P5'): (128, '63acada5', None, None, R_JUMP),
    ('Expander', 'E1-reset@block', 'P4'): (16, '374c116a', None, None, R_STATE),
    ('Expander', 'E1-reset@part', 'P4'): (16, '5e4aff57', None, None, R_STATE),
    ('Expander', 'E11-', 'P5'): (4, '83adb352', None, None, R_JUMP),
    ('Expander', 'E2-reset_buffer', 'P4'): (16, 'ed5b5919', None, None, R_STATE),
    ('Expander', 'E4-', 'P5'): (8, '0de52e7a', None, None, R_JUMP),
    ('Expander', 'E6-', 'P4'): (4, 'c555ff9c', None, None, R_STATE),
    ('Fuzz', 'E10-macros', 'P4'): (4, '92e3f2ae', None, None, R_STATE),
    ('Fuzz', 'E10-mix0', 'P3'): (4, '1c2a8dc6', None, None, R_FUZZ_WANDER),
    ('Fuzz', 'E10-patch', 'P3'): (4, '617e432c', None, None, R_FUZZ_WANDER),
    ('Fuzz', 'E10-patch', 'P4'): (4, 'f73d24bd', None, None, R_FUZZ_LEAN),
    ('Fuzz', 'E10-reset', 'P4'): (4, '0785c28c', None, None, R_STATE),
    ('Fuzz', 'E11-', 'P4'): (16, '67c5faea', None, None, R_FUZZ_LEAN),
    ('Fuzz', 'E11-', 'P5'): (2, 'ee31ffec', None, None, R_JUMP),
    ('Fuzz', 'E4-', 'P4'): (32, 'd667b376', None, None, R_STATE),
    ('Fuzz', 'E4-', 'P5'): (8, '51237885', None, None, R_JUMP),
    ('Fuzz', 'E5-mix0', 'P3'): (4, '785ac763', None, None, R_FUZZ_WANDER),
    ('Fuzz', 'E5-mix0', 'P4'): (36, '70f1f6b6', None, None, R_STATE),
    ('Fuzz', 'E5-mix0', 'P5'): (10, '0df66d65', None, None, R_JUMP),
    ('Fuzz', 'E6-', 'P3'): (8, 'f027b35d', None, None, R_FUZZ_WANDER),
    ('Fuzz', 'E6-', 'P4'): (90, '8332ee90', None, None, R_FUZZ_LEAN),
    ('Fuzz', 'E6-', 'P5'): (36, 'b27d3336', None, None, R_JUMP),
    ('Fuzz', 'E9-', 'P3'): (16, 'a4652cfe', None, None, R_FUZZ_WANDER),
    ('Fuzz', 'E9-', 'P4'): (192, '1cf6be45', None, None, R_STATE),
    ('Fuzz', 'E9-', 'P5'): (26, '95969050', None, None, R_JUMP),
    ('GraphicEQ', 'E11-', 'P5'): (8, '5e87946e', None, None, R_JUMP),
    ('GraphicEQ', 'E2-reset_buffer', 'P4'): (12, '17431038', None, None, R_STATE),
    ('GraphicEQ', 'E4-', 'P5'): (94, 'eee9b9a1', None, None, R_JUMP),
    ('GraphicEQ', 'E6-', 'P4'): (28, 'df3917fc', None, None, R_STATE),
    ('GraphicEQ', 'E6-', 'P5'): (60, 'fc0f3765', None, None, R_JUMP),
    ('HighPass', 'E1-reset@block', 'P4'): (21, 'd9891c63', None, None, R_STATE),
    ('HighPass', 'E1-reset@part', 'P4'): (21, 'af7690b3', None, None, R_STATE),
    ('HighPass', 'E11-', 'P4'): (16, '4fcdffe4', None, None, R_STATE),
    ('HighPass', 'E11-', 'P5'): (12, '4a25493b', None, None, R_JUMP),
    ('HighPass', 'E2-reset_buffer', 'P4'): (8, 'd1d172ed', None, None, R_STATE),
    ('HighPass', 'E4-', 'P4'): (16, 'd39c8c68', None, None, R_STATE),
    ('HighPass', 'E4-', 'P5'): (20, '4a07d152', None, None, R_JUMP),
    ('HighPass', 'E5-mix0', 'P4'): (12, 'c4ed62c2', None, None, R_STATE),
    ('HighPass', 'E5-mix0', 'P5'): (28, '1fcb9bb8', None, None, R_JUMP),
    ('HighPass', 'E6-', 'P4'): (55, 'e363a25b', None, None, R_STATE),
    ('HighPass', 'E6-', 'P5'): (58, '2d34599a', None, None, R_JUMP),
    ('HighPass', 'E9-', 'P4'): (60, '35dd8111', None, None, R_STATE),
    ('HighPass', 'E9-', 'P5'): (140, 'd9ed43e6', None, None, R_JUMP),
    ('LadderFilter', 'E10-mix0', 'P3'): (4, 'b6574e03', None, None, R_LADDER_OSC),
    ('LadderFilter', 'E4-', 'P5'): (26, 'f2142be7', None, None, R_JUMP),
    ('LadderFilter', 'E5-mix0', 'P3'): (4, '5df6ec0e', None, None, R_LADDER_OSC),
    ('LadderFilter', 'E5-mix0', 'P5'): (30, '87c00d0a', None, None, R_JUMP),
    ('LadderFilter', 'E6-', 'P5'): (58, 'f6d58cc2', None, None, R_JUMP),
    ('LadderFilter', 'E9-', 'P3'): (16, '4978cfa6', None, None, R_LADDER_OSC),
    ('LadderFilter', 'E9-', 'P5'): (150, '638865df', None, None, R_JUMP),
    ('Limiter', 'E11-', 'P5'): (4, '3b25af0f', None, None, R_JUMP),
    ('Limiter', 'E4-', 'P5'): (12, 'c136df4f', None, None, R_JUMP),
    ('Limiter', 'E6-', 'P4'): (12, 'aa0deac1', None, None, R_STATE),
    ('Limiter', 'E6-', 'P5'): (64, '851616ce', None, None, R_JUMP),
    ('LowPass', 'E11-', 'P5'): (8, '63b62611', None, None, R_JUMP_THUMP),
    ('LowPass', 'E2-reset_buffer', 'P4'): (8, '960b8f7c', None, None, R_STATE),
    ('LowPass', 'E4-', 'P5'): (20, 'd60ee44c', None, None, R_JUMP),
    ('LowPass', 'E4-m0=', 'P5'): (4, 'ce455454', None, None, R_THUMP),
    ('LowPass', 'E5-mix0', 'P4'): (11, '17e9bc9b', None, None, R_STATE),
    ('LowPass', 'E5-mix0', 'P5'): (18, 'fe3523d4', None, None, R_JUMP),
    ('LowPass', 'E6-', 'P4'): (20, '48ecf86c', None, None, R_STATE),
    ('LowPass', 'E6-', 'P5'): (60, 'fef0af21', None, None, R_JUMP_THUMP),
    ('LowPass', 'E9-', 'P4'): (55, '1389130d', None, None, R_STATE),
    ('LowPass', 'E9-', 'P5'): (90, '308dbe2d', None, None, R_JUMP),
    ('MultibandCompressor', 'E1-reset@block', 'P4'): (18, '2ff6f235', None, None, R_STATE),
    ('MultibandCompressor', 'E1-reset@part', 'P4'): (18, '79006c73', None, None, R_STATE),
    ('MultibandCompressor', 'E11-', 'P4'): (12, 'cdb143fb', None, None, R_STATE),
    ('MultibandCompressor', 'E11-', 'P5'): (12, '1035a853', None, None, R_JUMP),
    ('MultibandCompressor', 'E4-', 'P4'): (14, 'c26c22e5', None, None, R_STATE),
    ('MultibandCompressor', 'E4-', 'P5'): (57, '4819cc96', None, None, R_JUMP),
    ('MultibandCompressor', 'E5-mix0', 'P4'): (21, '54656bb3', None, None, R_STATE),
    ('MultibandCompressor', 'E5-mix0', 'P5'): (24, '8123a02d', None, None, R_JUMP),
    ('MultibandCompressor', 'E6-', 'P4'): (37, 'e0c88549', None, None, R_STATE),
    ('MultibandCompressor', 'E6-', 'P5'): (47, '18ab5a23', None, None, R_JUMP),
    ('MultibandCompressor', 'E9-', 'P4'): (84, '94963081', None, None, R_STATE),
    ('MultibandCompressor', 'E9-', 'P5'): (120, 'ced26bbc', None, None, R_JUMP),
    ('NoiseGate', 'E1-reset@block', 'P4'): (14, '8e201f94', None, None, R_STATE),
    ('NoiseGate', 'E1-reset@part', 'P4'): (14, 'b8240548', None, None, R_STATE),
    ('NoiseGate', 'E2-reset_buffer', 'P4'): (10, '5e5004a0', None, None, R_STATE),
    ('NoiseGate', 'E4-', 'P5'): (4, '00a5daae', None, None, R_JUMP),
    ('Notch', 'E11-', 'P5'): (8, 'f16f9e6c', None, None, R_JUMP_THUMP),
    ('Notch', 'E4-', 'P5'): (22, '66e5ec00', None, None, R_JUMP),
    ('Notch', 'E4-m0=', 'P5'): (8, 'a722c1dc', None, None, R_THUMP),
    ('Notch', 'E6-', 'P4'): (19, 'b648e1a5', None, None, R_STATE),
    ('Notch', 'E6-', 'P5'): (58, '48f66084', None, None, R_JUMP_THUMP),
    ('Overdrive', 'E1-reset@block', 'P4'): (34, 'aaf11cd2', None, None, R_STATE),
    ('Overdrive', 'E1-reset@part', 'P4'): (34, '75164359', None, None, R_STATE),
    ('Overdrive', 'E10-macros', 'P4'): (4, 'ca627259', None, None, R_STATE),
    ('Overdrive', 'E10-mix0', 'P4'): (2, '170e6132', None, None, R_STATE),
    ('Overdrive', 'E10-mix0', 'PR'): (2, 'acc31d24', None, None, R_142),
    ('Overdrive', 'E10-patch', 'P4'): (4, 'a20f495c', None, None, R_STATE),
    ('Overdrive', 'E10-reset', 'P4'): (4, '34caff5e', None, None, R_STATE),
    ('Overdrive', 'E11-', 'P4'): (8, '294ebbde', None, None, R_STATE),
    ('Overdrive', 'E11-', 'P5'): (2, '51122eee', None, None, R_JUMP),
    ('Overdrive', 'E4-', 'P4'): (16, 'b10db851', None, None, R_STATE),
    ('Overdrive', 'E4-', 'P5'): (4, '552de26f', None, None, R_JUMP),
    ('Overdrive', 'E5-mix0', 'P4'): (18, '60d901f0', None, None, R_STATE),
    ('Overdrive', 'E5-mix0', 'P5'): (16, '5e835e27', None, None, R_JUMP),
    ('Overdrive', 'E5-mix0', 'PR'): (2, 'd8985f28', None, None, R_142),
    ('Overdrive', 'E6-', 'P4'): (44, 'f84cecd5', None, None, R_STATE),
    ('Overdrive', 'E6-', 'P5'): (6, 'fa51be86', None, None, R_JUMP),
    ('Overdrive', 'E9-', 'P4'): (90, 'e2899302', None, None, R_STATE),
    ('Overdrive', 'E9-', 'P5'): (63, '63f22e1f', None, None, R_JUMP),
    ('ParametricEQ', 'E11-', 'P5'): (4, 'b81844e6', None, None, R_JUMP),
    ('ParametricEQ', 'E4-', 'P5'): (48, 'ca4d8e96', None, None, R_JUMP),
    ('ParametricEQ', 'E6-', 'P4'): (18, '364c9c07', None, None, R_STATE),
    ('ParametricEQ', 'E6-', 'P5'): (66, '8c801342', None, None, R_JUMP),
    ('Phaser', 'E1-reset@block', 'P4'): (40, 'eca258f1', None, None, R_PHASE),
    ('Phaser', 'E1-reset@part', 'P4'): (40, '54e5b3be', None, None, R_PHASE),
    ('Phaser', 'E11-', 'P4'): (16, '3eec4c9a', None, None, R_PHASE),
    ('Phaser', 'E11-', 'P5'): (8, '2408ab3c', None, None, R_JUMP),
    ('Phaser', 'E4-', 'P4'): (24, '7eca4736', None, None, R_PHASE),
    ('Phaser', 'E4-', 'P5'): (24, '8e313415', None, None, R_JUMP),
    ('Phaser', 'E5-mix0', 'P5'): (40, '343f01b2', None, None, R_JUMP),
    ('Phaser', 'E6-', 'P4'): (76, '520373a6', None, None, R_PHASE),
    ('Phaser', 'E6-', 'P5'): (86, '0a39c5d0', None, None, R_JUMP),
    ('Phaser', 'E9-', 'P5'): (200, 'f4918799', None, None, R_JUMP),
    ('RingMod', 'E1-reset@block', 'P4'): (40, '5f037604', None, None, R_PHASE),
    ('RingMod', 'E1-reset@part', 'P4'): (40, '4cdc6f50', None, None, R_PHASE),
    ('RingMod', 'E11-', 'P4'): (16, 'fb67e9fc', None, None, R_PHASE),
    ('RingMod', 'E11-', 'P5'): (12, '697ade72', None, None, R_JUMP),
    ('RingMod', 'E4-', 'P4'): (8, '97e3e000', None, None, R_PHASE),
    ('RingMod', 'E4-', 'P5'): (34, 'ee53bb96', None, None, R_JUMP),
    ('RingMod', 'E5-mix0', 'P5'): (28, 'c504653d', None, None, R_JUMP),
    ('RingMod', 'E6-', 'P4'): (96, '862d0a32', None, None, R_PHASE),
    ('RingMod', 'E6-', 'P5'): (44, 'aefba1ae', None, None, R_JUMP),
    ('RingMod', 'E9-', 'P5'): (140, 'f09d9cee', None, None, R_JUMP),
    ('Saturation', 'E11-', 'P5'): (10, 'f86a3f39', None, None, R_JUMP),
    ('Saturation', 'E4-', 'P5'): (48, 'f77cbcde', None, None, R_JUMP),
    ('Saturation', 'E5-mix0', 'P5'): (40, 'fc14e42e', None, None, R_JUMP),
    ('Saturation', 'E6-', 'P5'): (94, 'c9c25f1c', None, None, R_JUMP),
    ('Saturation', 'E9-', 'P5'): (184, '559386b8', None, None, R_JUMP),
    ('TransientShaper', 'E11-', 'P5'): (8, '24eee129', None, None, R_JUMP),
    ('TransientShaper', 'E2-reset_buffer', 'P4'): (22, 'bee31922', None, None, R_STATE),
    ('TransientShaper', 'E4-', 'P5'): (22, 'f1638686', None, None, R_JUMP),
    ('TransientShaper', 'E6-', 'P4'): (22, 'a20cab27', None, None, R_STATE),
    ('TransientShaper', 'E6-', 'P5'): (68, '858e96a7', None, None, R_JUMP),
    ('Tremolo', 'E11-', 'P4'): (8, '6a7b6d8e', None, None, R_PHASE),
    ('Tremolo', 'E11-', 'P5'): (4, 'dc306763', None, None, R_JUMP),
    ('Tremolo', 'E4-', 'P4'): (12, '058ac2bd', None, None, R_PHASE),
    ('Tremolo', 'E4-', 'P5'): (8, '40b3336d', None, None, R_JUMP),
    ('Tremolo', 'E6-', 'P4'): (92, 'a3a22dcf', None, None, R_PHASE),
    ('Tremolo', 'E6-', 'P5'): (33, 'dc1bc985', None, None, R_JUMP),
    ('Vibrato', 'E11-', 'P4'): (12, '4204b137', None, None, R_PHASE),
    ('Vibrato', 'E2-reset_buffer', 'P4'): (32, 'a6de06f2', None, None, R_PHASE),
    ('Vibrato', 'E4-', 'P4'): (8, 'f6a551f6', None, None, R_PHASE),
    ('Vibrato', 'E4-', 'P5'): (6, '3c699fea', None, None, R_JUMP),
    ('Vibrato', 'E6-', 'P4'): (52, 'b9c53ae9', None, None, R_PHASE),
}

#: CircuitPython's own nodes answer the host's `reset_buffer` differently
#: from audiodsp's port, so E2 renders other bytes there with the same
#: verdicts (audiocomponents#158). class -> (quick cells, digest, full
#: cells, digest, reason).
_CP_RESET_BUFFER = (
    "CircuitPython's own nodes answer the host's reset_buffer differently"
    " from audiodsp's port: other bytes, the same verdicts"
    " (audiocomponents#158)")
KNOWN_P6 = {
    "Compressor": (4, "70d574f2", None, None, _CP_RESET_BUFFER),
    "Distortion": (48, "950b4395", None, None, _CP_RESET_BUFFER),
    "Exciter": (32, "4f3d4cfb", None, None, _CP_RESET_BUFFER),
    "MultibandCompressor": (5, "83a48f4f", None, None, _CP_RESET_BUFFER),
    "Overdrive": (18, "ae64809f", None, None, _CP_RESET_BUFFER),
}
