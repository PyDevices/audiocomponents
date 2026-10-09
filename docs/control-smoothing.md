# Smoothing control moves

When a control jumps, the effects hand the new value to their nodes at once,
and the output steps. You hear a click. That happens on a patch change, on a
MIDI value that leaps, or when a host sets Mix from 0.3 to 1.0 in one call. A
knob turned by hand sends many small moves, so it sounds smooth already. Until
the policy below lands, send a jump as small steps, one a block, if you need it
smooth: the delays' own tests show Mix moved in 127 steps, one a block, steps
the output by less than one and a half times the steepest step of the tone
going through it.

This page is the policy the effects will follow. Nothing on it is built yet.

## Which controls ramp, and for how long

Every control that scales a signal ramps: Mix, Level and Volume, a wet or dry
gain, and a modulation depth. A move ramps in a straight line over 20 ms, the
time `audioecho.FeedbackDelay` already takes for its wow depth. That is short
enough to sound like the knob you turned. Whether it is long enough to take
the click out of every jump is the step property's to say (below), once the
ramp is built.

A delay's Time is not ramped here: it already glides, at the rate its Glide
control sets. A filter corner that jumps steps the output too, more quietly
than a level does; it comes after the levels, with the node moving its
coefficients across the same 20 ms.

A switch, or a patch change that rebuilds part of a graph, crossfades from the
old graph to the new over the same 20 ms instead of cutting.

## Where the ramp lives

In the nodes, in audiodsp. A ramp has to move once a sample to be smooth, and
an effect class runs Python only when a control is called, never while its
output is pulled. A ramp stepped from Python moves once a block at best, and
only if the host calls something every block. Built into the node, the ramp
costs a multiply a sample, runs on every interpreter and every board, and
reaches anyone using the bare nodes too, CircuitPython users included.

Mix comes first, because it is the control most likely to be jumped and the
loudest when it is.

## When it is done

The lifecycle matrix's step property (P5 in
[`tests/support/LIFECYCLE.md`](../tests/support/LIFECYCLE.md)) holds for every
class with no exception declared for a control that jumps, and each class's
docstring drops the sentence that says a jump steps the output.
