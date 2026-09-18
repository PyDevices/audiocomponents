#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
NGSPICE=${NGSPICE:-/usr/bin/ngspice}
mkdir -p out
rm -f out/*.csv out/*.log
"$NGSPICE" -b rat_clip.cir -o out/ngspice_clip.log
"$NGSPICE" -b rat_gain.cir -o out/ngspice_gain.log
for f in out/*.csv; do
    sed -i -E 's/^[[:space:]]+//; s/[[:space:]]+$//; s/[[:space:]]+/,/g' "$f"
done
if grep -il 'error' out/ngspice_*.log >/dev/null; then
    echo "run.sh: ngspice reported errors" >&2
    grep -in 'error' out/ngspice_*.log >&2
    exit 1
fi
echo "run.sh: wrote $(ls out/*.csv | wc -l) CSV files into $(pwd)/out"
ls -l out/*.csv
