#!/usr/bin/env bash
# run.sh -- simulate the TS808 drive and tone stages under ngspice -b and
# leave CSVs in out/.  Then: <python-with-numpy> analyze.py
#
#   out/drive_tran_pos{0,0.5,1}_amp{0.05,0.2,0.5}.csv   time, v(out), v(inp)
#   out/drive_ac_posmax.csv                             frequency, vdb(out), vp(out)  [vp = radians]
#   out/tone_ac_tone{0,0.5,1}.csv                       frequency, vdb(tout), vp(tout), vdb(lv), vp(lv)  [vp = radians]
#   out/ngspice_drive.log, out/ngspice_tone.log         ngspice's own output
#
# ngspice's wrdata writes whitespace-separated columns; the sed pass below
# turns them into comma-separated ones so the .csv name is honest.
set -euo pipefail
cd "$(dirname "$0")"
NGSPICE=${NGSPICE:-/usr/bin/ngspice}

mkdir -p out
rm -f out/*.csv out/*.log

"$NGSPICE" -b ts808_drive.cir -o out/ngspice_drive.log
"$NGSPICE" -b ts808_tone.cir  -o out/ngspice_tone.log

for f in out/*.csv; do
    sed -i -E 's/^[[:space:]]+//; s/[[:space:]]+$//; s/[[:space:]]+/,/g' "$f"
done

if grep -il 'error' out/ngspice_*.log >/dev/null; then
    echo "run.sh: ngspice reported errors -- see out/ngspice_*.log" >&2
    grep -in 'error' out/ngspice_*.log >&2
    exit 1
fi

n=$(ls out/*.csv | wc -l)
echo "run.sh: wrote $n CSV files into $(pwd)/out"
ls -l out/*.csv
