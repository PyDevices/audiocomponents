"""Instruments built on two threads at once each keep their own keyboards.

An instrument factory hands its synthesizer's `Keys` to the `Instrument` it
ends with. When two threads run factories at the same time, a `Keys` made on
one thread must not end up in the other thread's instrument.
"""
import threading
import unittest

from audioinstruments import _support


def _instrument(synth):
    return _support.Instrument(synth, lambda *a: None, {0: ("Default", ())}, ())


class InstrumentThreadsTest(unittest.TestCase):
    def test_factories_on_two_threads_keep_their_own_keyboards(self):
        made_a = threading.Event()
        b_done = threading.Event()
        got = {}

        def factory_a():
            synth = _support.synthesizer(48000, 1)
            made_a.set()
            b_done.wait(5)                 # thread B builds a whole instrument now
            got["a"] = (synth, _instrument(synth))

        def factory_b():
            made_a.wait(5)
            synth = _support.synthesizer(48000, 1)
            got["b"] = (synth, _instrument(synth))
            b_done.set()

        ta = threading.Thread(target=factory_a)
        tb = threading.Thread(target=factory_b)
        ta.start(); tb.start(); ta.join(10); tb.join(10)
        for name in ("a", "b"):
            synth, inst = got[name]
            self.assertEqual(inst._keys, (synth,), "instrument %s took another thread's keyboard" % name)


if __name__ == "__main__":
    unittest.main()
