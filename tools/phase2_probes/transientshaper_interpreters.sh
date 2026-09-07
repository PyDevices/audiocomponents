#!/bin/sh
# Station C's cross-interpreter leg for TransientShaper: render the same
# probes on all three interpreters with tools/render_effect.py, into
# per-interpreter directories, so the CPython analyser can compare bytes.
#
#   sh tools/phase2_probes/transientshaper_interpreters.sh <outdir>
#
# The analysis is CPython's (kit spec section 1); this file only renders.
set -e
ROOT=$(cd "$(dirname "$0")/../.." && pwd)
OUT=${1:-$ROOT/../ts-renders}
CMODS=$(cd "$ROOT/../cmods" && pwd)
VENV=$(cd "$ROOT/../audiocomponents/.venv/bin" && pwd)/python

cd "$ROOT"
for RATE in 48000 44100 22050; do
  for CASE in "ramp_fs" "noise_det" "click_stereo" "chord" "sweep_log"; do
    for INTERP in cpython micropython circuitpython-effects; do
      case $INTERP in
        cpython) RUN="env PYTHONPATH=$ROOT/lib $VENV" ;;
        micropython) RUN="env MICROPYPATH=lib:$CMODS/micropython/lib $CMODS/bin/micropython" ;;
        *) RUN="env MICROPYPATH=lib:$CMODS/micropython/lib $CMODS/bin/circuitpython-effects -X heapsize=256M" ;;
      esac
      $RUN tools/render_effect.py TransientShaper "$CASE" "$OUT/$INTERP" \
        --rate "$RATE" --channels 2 --block 256 >/dev/null
    done
  done
  # The working state, not the wire: Attack +12, Sustain -12.
  for INTERP in cpython micropython circuitpython-effects; do
    case $INTERP in
      cpython) RUN="env PYTHONPATH=$ROOT/lib $VENV" ;;
      micropython) RUN="env MICROPYPATH=lib:$CMODS/micropython/lib $CMODS/bin/micropython" ;;
      *) RUN="env MICROPYPATH=lib:$CMODS/micropython/lib $CMODS/bin/circuitpython-effects -X heapsize=256M" ;;
    esac
    $RUN tools/render_effect.py TransientShaper burst_silence "$OUT/$INTERP" \
      --rate "$RATE" --channels 2 --block 256 --macro 0=114.3 --macro 1=31.75 \
      >/dev/null
    # And a musical probe with the shaper working, so the digest table is
    # not four readings of the wire.
    for CASE in chord noise_det; do
      $RUN tools/render_effect.py TransientShaper "$CASE" "$OUT/$INTERP" \
        --rate "$RATE" --channels 2 --block 256 --patch 1 >/dev/null
    done
  done
done
echo "rendered into $OUT/{cpython,micropython,circuitpython-effects}"
