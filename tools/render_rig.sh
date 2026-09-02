#!/usr/bin/env bash
# Generate a named instrument's rig project, stage accuracy's OWN
# lib/audioinstruments (and lib/audioeffects) over the installed VST3
# bundle so the plug-in runs this repo's code rather than audioif's frozen
# copy, then render it headlessly through REAPER and through this repo's
# offline CPython renderer, and compare the two.
#
#   tools/render_rig.sh <instrument>
#
# Needs: the plug-in installed for Windows already
# (micropython-vst3/scripts/install-plugin-windows.sh, after rebuilding the
# sidecar engine if audioif's C changed - see AUDIOIF_PIN and
# micropython-vst3's own hazard notes; this script does not do either of
# those, on purpose - they are not "every render", they are "audioif
# changed").
set -euo pipefail

instrument=${1:?usage: render_rig.sh <instrument>}

repo_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
tools_dir="$repo_dir/tools"
build_dir="$repo_dir/build/rig"
vst3_repo=$(cd "$repo_dir/../micropython-vst3" && pwd)

venv_python="$repo_dir/.venv/bin/python"
[[ -x "$venv_python" ]] || { echo "error: no venv at $repo_dir/.venv - see README" >&2; exit 1; }

source "$vst3_repo/scripts/windows-paths.sh"
mpvst_load_windows_paths || exit 1

reaper_exe=${REAPER_EXE:-$WIN_USERPROFILE/REAPER/reaper.exe}
test -e "$reaper_exe" || { echo "error: REAPER not found at $reaper_exe" >&2; exit 1; }
test -x "$reaper_exe" || chmod +x "$reaper_exe"

# Portable-vs-AppData resource dir: a reaper.ini beside the exe means
# REAPER is running portable and reads Scripts/ from there, never AppData -
# guessing wrong leaves the startup hook somewhere REAPER never looks
# (micropython-vst3's own documented hazard). Verified 2026-09-02 against
# this machine: reaper.ini exists in BOTH places, and the one beside the
# exe wins.
if [[ -n "${REAPER_RESOURCE:-}" ]]; then
    reaper_resource=$REAPER_RESOURCE
elif [[ -f "$(dirname "$reaper_exe")/reaper.ini" ]]; then
    reaper_resource=$(dirname "$reaper_exe")
else
    reaper_resource=$WIN_APPDATA/REAPER
fi

bundle=${MPVST_VST3_DIR:-$WIN_LOCALAPPDATA/Programs/Common/VST3}/MicroPythonVST3.vst3
test -d "$bundle" || { echo "error: MicroPythonVST3.vst3 not installed at $bundle" >&2; exit 1; }
bundle_lib="$bundle/Contents/x86_64-win"

cmake_exe="$vst3_repo/.deps/cmake-4.4.2-windows-x86_64/bin/cmake.exe"
test -x "$cmake_exe" || { echo "error: vendored cmake missing at $cmake_exe" >&2; exit 1; }

stop_reaper() {
    powershell.exe -NoProfile -Command \
        "Get-Process reaper,micropython-vst-engine -EA SilentlyContinue | Stop-Process -Force -EA SilentlyContinue" \
        >/dev/null 2>&1 || true
}

mkdir -p "$build_dir"

echo "--- 1. generating the rig project ---"
"$venv_python" "$tools_dir/generate_rig.py" "$instrument" \
    "$build_dir/${instrument}_rig.RPP"

echo
echo "--- 2. staging accuracy's own lib/ over the installed bundle ---"
echo "    (so the plug-in runs THIS repo's audioinstruments/audioeffects," \
     "not audioif's frozen copy - reversible, and repeated every render)"
"$cmake_exe" -DMPVST_LIB_SRC="$(wslpath -w "$repo_dir/lib")" \
    -DMPVST_LIB_DST="$(wslpath -w "$bundle_lib")" \
    -P "$(wslpath -w "$vst3_repo/src/plugin/stage_lib.cmake")"
diff -q "$repo_dir/lib/audioinstruments/${instrument}.py" \
        "$bundle_lib/audioinstruments/${instrument}.py" >/dev/null \
    && echo "    staged: bundle's ${instrument}.py == accuracy's lib/ (byte-identical)" \
    || { echo "error: stage did not land - bundle disagrees with lib/" >&2; exit 1; }

echo
echo "--- 3. offline CPython render (this repo's own code, direct) ---"
"$venv_python" "$tools_dir/render_rig_offline.py" "$instrument" \
    "$build_dir/${instrument}_offline.wav"

echo
echo "--- 4. headless REAPER render through the plug-in ---"
work_unix="$WIN_TEMP/mpvst-rig-$instrument"
rm -rf "$work_unix"
mkdir -p "$work_unix"
work_native=$(wslpath -w "$work_unix")
project_native=$(wslpath -w "$build_dir/${instrument}_rig.RPP")

echo "Stopping any running REAPER instance..."
stop_reaper
sleep 2

# Track/env counts come from generate_rig.py's own fixed shape
# (A, B, Play = 3 tracks) and the gesture module's own macro_env count,
# and render length is read straight out of the gesture module so a
# longer rig is never judged against a stale fixed deadline.
n_tracks=3
n_min_envs=$(cd "$repo_dir" && "$venv_python" - "$instrument" <<'PYEOF2'
import sys
sys.path.insert(0, "tools")
from generate_rig import load_gesture_module
m = load_gesture_module(sys.argv[1])
def dummy_measure(chord, vel, **kw):
    return 1.0
spec = m.build(dummy_measure)
print(len(spec["macro_env"]) * 2)
PYEOF2
)
render_seconds=$(cd "$repo_dir" && "$venv_python" - "$instrument" <<'PYEOF3'
import sys
sys.path.insert(0, "tools")
from generate_rig import load_gesture_module
m = load_gesture_module(sys.argv[1])
def dummy_measure(chord, vel, **kw):
    return 1.0
spec = m.build(dummy_measure)
print(spec["total_seconds"] + 4.0)
PYEOF3
)

mkdir -p "$reaper_resource/Scripts"
cp "$tools_dir/rig_verify.lua" "$reaper_resource/Scripts/__startup.lua"

launcher="$WIN_TEMP/mpvst_rig_${instrument}.ps1"
cat > "$launcher" <<PS1
\$env:MPVST_RIG_REPORT = "$work_native\\report.txt"
\$env:MPVST_RIG_WORKDIR = "$work_native"
\$env:MPVST_RIG_SECONDS = "$render_seconds"
\$env:MPVST_RIG_BOUNCE = "${instrument}_bounce"
\$env:MPVST_RIG_TRACKS = "$n_tracks"
\$env:MPVST_RIG_MIN_ENVS = "$n_min_envs"
\$env:MPVST_RIG_DEADLINE = "600"
Start-Process -FilePath "$(wslpath -w "$reaper_exe")" -ArgumentList "-ignoreerrors","$project_native"
PS1
echo "Launching headless render (timeout 600s)..."
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$(wslpath -w "$launcher")" \
    >/dev/null 2>&1 || true

deadline=$(( $(date +%s) + 600 ))
grace=180
started=$(date +%s)
while [ "$(date +%s)" -lt "$deadline" ]; do
    if [ -f "$work_unix/report.txt" ]; then
        grep -q '^DONE' "$work_unix/report.txt" 2>/dev/null && break
    elif [ $(( $(date +%s) - started )) -gt "$grace" ]; then
        stop_reaper
        rm -f "$reaper_resource/Scripts/__startup.lua"
        echo "error: no report after ${grace}s - startup hook never ran" >&2
        exit 1
    fi
    sleep 5
done

stop_reaper
rm -f "$reaper_resource/Scripts/__startup.lua"

echo
echo "=== rig verification report ==="
cat "$work_unix/report.txt" 2>/dev/null || echo "no report produced"

bounce="$work_unix/${instrument}_bounce.wav"
if [ -f "$bounce" ]; then
    cp "$bounce" "$build_dir/${instrument}_bounce.wav"
    echo "wrote $build_dir/${instrument}_bounce.wav"
else
    echo "error: no bounce produced" >&2
    exit 1
fi

echo
echo "--- 5. comparing plug-in bounce against the offline render ---"
"$venv_python" "$tools_dir/compare_rig.py" "$build_dir/${instrument}_rig.RPP" \
    "$build_dir/${instrument}_bounce.wav" "$build_dir/${instrument}_offline.wav"
