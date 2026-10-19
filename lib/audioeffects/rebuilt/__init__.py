"""Old import paths, kept working.

The delay, reverb, pitch and rack classes used to live here. Each now has
its own module directly under `audioeffects` (`audioeffects.reverb`,
`audioeffects.digitaldelay`, ...), and `from audioeffects import Reverb`
is the way to reach one. `audioeffects.rebuilt.<module>` still imports the
same class from its new home, so code written against the old path keeps
running. Nothing in the package imports this one.
"""
