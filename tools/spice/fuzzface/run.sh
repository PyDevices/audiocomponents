#!/usr/bin/env bash
# Three 1 kHz transients at Fuzz pot 1 / 500 / 1000 ohm, plus one AC sweep.
set -euo pipefail
cd "$(dirname "$0")"
NGSPICE=${NGSPICE:-/usr/bin/ngspice}
mkdir -p out
rm -f out/*.csv out/*.log

for fuzz in 1 500 1000; do
    sed "s/{fuzz}/$fuzz/" fuzzface.cir > out/run_$fuzz.cir
    # wrdata path unique per setting
    sed -i "s|out/tran_fuzz500.csv|out/tran_fuzz${fuzz}.csv|" out/run_$fuzz.cir
    "$NGSPICE" -b out/run_$fuzz.cir -o out/ngspice_$fuzz.log
done

for f in out/*.csv; do
    [ -f "$f" ] || continue
    sed -i -E 's/^[[:space:]]+//; s/[[:space:]]+$//; s/[[:space:]]+/,/g' "$f"
done

if grep -il 'error' out/ngspice_*.log >/dev/null; then
    echo "run.sh: ngspice reported errors -- see out/ngspice_*.log" >&2
    grep -in 'error' out/ngspice_*.log >&2
    exit 1
fi
echo "ok: CSVs in out/"
