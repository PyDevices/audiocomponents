# Sound stability

The API is the contract: class names, signatures, metadata and macro surfaces
stay stable and change only deliberately. The *sound* is not part of that
contract. These components sound good, but they are not all as accurate as they
could be, and implementations keep being refined as the library matures, so a
component may render audibly differently from one release to the next. If a
composition depends on the exact sound of a release, pin that release rather
than tracking the latest.

Beneath the components sits a harder guarantee, and it is audiodsp's: the
CircuitPython-compatible `synthio`, `audiocore` and effects-module core is held
bit-exact to CircuitPython itself and does not change from release to release.
Where CircuitPython and audiodsp disagree, that is a bug and it is reported
upstream. The components are where the sound evolves; the floor they stand on
does not.
