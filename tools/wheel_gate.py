"""Build each package's wheel the way a release does, install it into a clean
venv, and play it.

    python tools/wheel_gate.py [--audiodsp SPEC]

The editable installs the test job uses cannot see a packaging mistake: they
serve lib/ straight off the disk, so a subpackage pyproject.toml forgets is
still importable there. v0.3.0 shipped exactly that -- the audioeffects wheel
left out `audioeffects.rebuilt`, and the published package failed on import.
This gate checks the artefact instead of the tree.

For each of lib/audioinstruments and lib/audioeffects it:

1. copies the package directory aside, writes the repo's VERSION into it (as
   the release reusable does) and runs `python -m build --wheel`;
2. fails if any .py file under the source directory is missing from the
   wheel;

then it makes one clean venv, installs audiodsp (default: the AUDIODSP_PIN
commit from git, as tests.yml does) and both wheels with --no-deps, and --
from outside the repo, with `python -I` so lib/ cannot leak in -- imports
both packages, renders one instrument and one effect by catalogue name, and
loads every rebuilt effect class.

Needs `build` in the interpreter that runs it. Exit status is non-zero on any
failure, and every failure is printed.
"""

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PACKAGES = ("audioinstruments", "audioeffects")

SMOKE = r'''
import sys
from array import array
import audiocore
import audioinstruments
import audioeffects
from audioeffects import rebuilt

for module in (audioinstruments, audioeffects):
    if "site-packages" not in module.__file__:
        sys.exit("%s imported from %s, not the installed wheel"
                 % (module.__name__, module.__file__))

RATE = 48000


def loudest(sample, blocks=8):
    peak = 0
    for _ in range(blocks):
        data = bytes(audiocore.get_buffer(sample)[1])
        for i in range(0, len(data) - 1, 2):
            value = int.from_bytes(data[i:i + 2], "little", signed=True)
            peak = max(peak, abs(value))
    return peak


instrument = audioinstruments.create("tr808", RATE)
instrument.note_on(36)
peak = loudest(instrument.output)
print("audioinstruments tr808 peak", peak)
if not peak:
    sys.exit("tr808 rendered silence")

values = array("h")
for frame in range(4096):
    values.append(((frame * 61) % 401 - 200) * 50)
    values.append(((frame * 78) % 401 - 200) * 50)
signal = audiocore.RawSample(values, sample_rate=RATE, channel_count=2)
effect = audioeffects.create("Flanger", signal, RATE)
peak = loudest(effect.output)
print("audioeffects Flanger peak", peak)
if not peak:
    sys.exit("Flanger rendered silence")

names = sorted(rebuilt.known())
if not names or any(rebuilt.module_class(name) is None for name in names):
    sys.exit("rebuilt effect classes did not load: %r" % (names,))
print("rebuilt classes load:", ", ".join(names))
print("wheel smoke: ok")
'''


def audiodsp_pin():
    for line in (ROOT / "AUDIODSP_PIN").read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            return line.split()[0]
    sys.exit("AUDIODSP_PIN has no pin line")


def run(*args, **kwargs):
    shown = ["<smoke script>" if a is SMOKE else str(a) for a in args]
    print("+", " ".join(shown), flush=True)
    return subprocess.run([str(a) for a in args], **kwargs)


def build_wheel(package, work):
    source = ROOT / "lib" / package
    staged = work / "src" / package
    shutil.copytree(source, staged, ignore=shutil.ignore_patterns(
        "__pycache__", "*.egg-info", "build", "dist"))
    shutil.copy(ROOT / "VERSION", staged / "VERSION")
    out = work / "dist"
    run(sys.executable, "-m", "build", "--wheel", "--outdir", out, staged,
        check=True, stdout=subprocess.DEVNULL)
    wheel = next(out.glob("pydevices_%s-*.whl" % package))

    expected = {package + "/" + path.relative_to(source).as_posix()
                for path in source.rglob("*.py")
                if "__pycache__" not in path.parts}
    with zipfile.ZipFile(wheel) as archive:
        shipped = set(archive.namelist())
    missing = sorted(expected - shipped)
    for name in missing:
        print("MISSING from %s: %s" % (wheel.name, name))
    print("%s: %d of %d source modules in the wheel"
          % (wheel.name, len(expected) - len(missing), len(expected)))
    return wheel, missing


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument(
        "--audiodsp",
        help="pip requirement for audiodsp (default: the AUDIODSP_PIN commit)")
    args = parser.parse_args()
    audiodsp = args.audiodsp or (
        "pydevices-audiodsp @ git+https://github.com/PyDevices/audiodsp@"
        + audiodsp_pin())

    failures = []
    with tempfile.TemporaryDirectory(prefix="wheel-gate-") as tmp:
        work = Path(tmp)
        wheels = []
        for package in PACKAGES:
            wheel, missing = build_wheel(package, work)
            wheels.append(wheel)
            if missing:
                failures.append("%s wheel is missing %d module(s)"
                                % (package, len(missing)))

        venv = work / "venv"
        run(sys.executable, "-m", "venv", venv, check=True)
        python = venv / ("Scripts/python.exe" if os.name == "nt"
                         else "bin/python")
        run(python, "-m", "pip", "install", "-q",
            "--disable-pip-version-check", audiodsp, check=True)
        run(python, "-m", "pip", "install", "-q",
            "--disable-pip-version-check", "--no-deps", *wheels, check=True)

        smoke = run(python, "-I", "-c", SMOKE, cwd=work)
        if smoke.returncode:
            failures.append("installed wheels failed the smoke run")

    for failure in failures:
        print("FAIL", failure)
    if failures:
        return 1
    print("wheel gate: ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
