"""`AirSpace`'s planted faults, one or two per trait of its card.

Kept apart from the test module, and free of numpy and unittest, so the
kit's plant-validity check runs them on MicroPython and CircuitPython too
(`tests/support/kit.py AirSpace --plants-module airspace_plants`). The test
module imports them from here and lists them in its own `KIT_PLANTS`.
"""

import audiobiquad

import audioeffects
from audioeffects import airspace as space

#: Read by `_component`'s metadata check off the module a class lives in.
VENDOR = "PyDevices"

AirSpace = audioeffects.AirSpace


class SendFirst(AirSpace):
    """T1: the Top Cut ahead of the Splitter, as the old rack had it, so the
    dry is filtered too; the send's own filter is left open."""

    def _build(self, *args, **options):
        self._pre = None
        AirSpace._build(self, *args, **options)
        self._pre = audiobiquad.Biquad(
            mode=audiobiquad.LOW_PASS,
            frequency=self._hz(self._value(space.TOP_CUT_I)),
            sample_rate=self._sample_rate, channel_count=self._channel_count)
        self._pre.play(self._source)
        self._adapter.play(self._pre)
        self._own(self._pre, reset=self._pre.clear)
        self._lp.frequency = self._hz(20000.0)

    def _apply_macro(self, index, position):
        AirSpace._apply_macro(self, index, position)
        pre = getattr(self, "_pre", None)
        if pre is not None and index == space.TOP_CUT_I:
            pre.frequency = self._hz(self._value(space.TOP_CUT_I))
            self._lp.frequency = self._hz(20000.0)


class LoopOnSend(AirSpace):
    """T2, first half: the loop's low-pass taken out of the loop and put on
    the send as a second Biquad, so every repeat is darkened alike."""

    def _build(self, *args, **options):
        self._loop_lp = None
        self._loop_hz = space.DEFAULTS[space.LOOP_TOP_I]
        AirSpace._build(self, *args, **options)
        self._loop_lp = audiobiquad.Biquad(
            mode=audiobiquad.LOW_PASS, frequency=self._loop_hz,
            sample_rate=self._sample_rate, channel_count=self._channel_count)
        self._loop_lp.play(self._fd)
        self._lp.play(self._loop_lp)
        self._own(self._loop_lp, reset=self._loop_lp.clear)

    def _hand_tape(self, **settings):
        if "damping_hz" in settings:
            self._loop_hz = settings["damping_hz"]
            settings["damping_hz"] = 0.0
            loop_lp = getattr(self, "_loop_lp", None)
            if loop_lp is not None:
                loop_lp.frequency = self._loop_hz
        AirSpace._hand_tape(self, **settings)


class TopCutInLoop(AirSpace):
    """T2, second half: Top Cut wired to the loop's low-pass instead of the
    send's filter, so it darkens each repeat more than the last."""

    def _apply_macro(self, index, position):
        AirSpace._apply_macro(self, index, position)
        if self._ready and index in (space.TOP_CUT_I, space.LOOP_TOP_I):
            self._hand_tape(damping_hz=self._hz(self._value(space.TOP_CUT_I)))
            self._lp.frequency = self._hz(20000.0)


class NoFeedback(AirSpace):
    """T3: the node is handed no feedback, whatever Feedback says."""

    def _hand_tape(self, **settings):
        if "feedback" in settings:
            settings["feedback"] = 0.0
        AirSpace._hand_tape(self, **settings)


class BareRepeats(AirSpace):
    """T4: the chamber is a wire: the repeats reach the output bare."""

    def _wet_source(self):
        return self._lp


class JumpTime(AirSpace):
    """T5: the node is handed no slew, so a Time move jumps."""

    def _hand_tape(self, **settings):
        if "delay_slew" in settings:
            settings["delay_slew"] = 0.0
        AirSpace._hand_tape(self, **settings)


#: The kit's plant table (KIT.md, plants). NoFeedback is judged at Long
#: Send: at the defaults it is what Feedback 0 renders, a setting rather
#: than a fault.
KIT_PLANTS = {
    "T1": SendFirst,
    "T2a": LoopOnSend,
    "T2b": TopCutInLoop,
    "T3": (NoFeedback, 2),
    "T4": BareRepeats,
    "T5": JumpTime,
}
