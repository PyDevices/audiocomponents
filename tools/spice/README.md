# SPICE references for the effects program

One directory per standout circuit. Each holds the netlists we wrote from a
schematic read for topology and values (a schematic on a hobby site is a
document — effects vision §5), a `run.sh` that runs them under `ngspice -b`
into a gitignored `out/`, an `analyze.py` that turns the CSVs into the
numbers a dossier cites, and a README with every source reached, the license
call per source, every simplification named, and the analysis output pasted
verbatim from a real run. Generated output is never committed; the README's
numbers are the record, and the run reproduces them in seconds.

The first, `ts808/`, is Phase 0's proof that the workflow works end to end.
