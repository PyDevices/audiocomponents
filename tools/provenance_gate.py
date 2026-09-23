"""Refuse a workspace `bin/` interpreter that does not contain the audiodsp this
repository's gates are read at.

[cmods#27](https://github.com/PyDevices/cmods/issues/27). A binary in
`bin/` reports MicroPython's own version and a build date and says
nothing about which audiodsp was compiled into it. On 2026-09-03 that cost a
week of green gates: `bin/micropython` was built at 01:16, an audiodsp C
change landed at 01:29, and every parity run after that certified a binary
that did not contain the code the gate was about. **A green gate on a stale
binary is the most expensive kind of stale**, because absence of a signal
reads as agreement.

`tools/provenance.py` (in the workspace anchor) writes a stamp beside every interpreter
`build_interpreters.sh` installs. This is the half our gates call.

The question this repository asks is not the one audiodsp's own gates ask.
Ours is pinned: `AUDIODSP_PIN` names the exact commit every gate here runs
against, and audiodsp's checkout moves several times a day for things our
gates are not about. So we ask **does this binary contain the pin**, not
"is it the checkout's HEAD" — a check that is red every day stops being
read. What it refuses is a binary built before the pin moved, which is
exactly the binary that cannot contain what the pin names.

It is a refusal, not a warning. A gate that prints "possibly stale" and runs
anyway has told nobody anything.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT.parent
PROVENANCE = WORKSPACE / "tools" / "provenance.py"
PIN_FILE = ROOT / "AUDIODSP_PIN"

#: Set to 1 to skip the check. There is no in-band way to do this on purpose,
#: and that is deliberate: it exists for a checkout with no cmods beside it,
#: not for a run that would rather not know.
SKIP = os.environ.get("AUDIOCOMPONENTS_SKIP_PROVENANCE") == "1"


def audiodsp_pin() -> str | None:
    """The commit in the last line of AUDIODSP_PIN (`<ref> <commit>`)."""
    if not PIN_FILE.is_file():
        return None
    for line in reversed(PIN_FILE.read_text(encoding="utf-8").splitlines()):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        return parts[-1] if parts else None
    return None


def check(binary) -> tuple[bool, str]:
    """(ok, message) for one interpreter. Unknown is not OK."""
    binary = Path(binary)
    if SKIP:
        return True, f"{binary.name}: provenance check skipped by the environment"
    if not PROVENANCE.is_file():
        # No cmods beside us. Say so out loud rather than passing quietly: a
        # skip that looks like a pass is the failure this check is about.
        return False, (
            f"cannot check {binary.name}'s provenance: no {PROVENANCE}. "
            f"This interpreter may have been built from any audiodsp.")
    pin = audiodsp_pin()
    if pin is None:
        return False, f"cannot read a commit out of {PIN_FILE}"
    argv = [sys.executable, str(PROVENANCE), "check", str(binary),
            "--source", "audiodsp", "--contains", f"audiodsp={pin}"]
    done = subprocess.run(argv, capture_output=True, text=True)
    return done.returncode == 0, (done.stdout + done.stderr).strip()


def require(binary) -> None:
    """Refuse, loudly, or return. For a runner with a main()."""
    ok, message = check(binary)
    print(message)
    if not ok:
        raise SystemExit(
            f"\n{binary} cannot certify this repository: it does not contain "
            f"the audiodsp in AUDIODSP_PIN.\n"
            f"Rebuild it:  ../tools/build_interpreters.sh --only mp-unix\n"
            f"(cp-unix for circuitpython.)\n")
