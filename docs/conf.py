"""Sphinx configuration for the audiocomponents documentation.

Everything shared by the PyDevices documentation projects (theme, top bar,
Markdown and docstring setup, the reference map) comes from pydevices-docs.
"""

from pydevices_docs import configure

settings = configure(
    "audiocomponents", __file__,
    repo="PyDevices/audiocomponents", edit_path="docs",
    source_dirs=["../lib"],
    api_packages=["audioinstruments", "audioeffects"],
    # audiodsp's native modules are not installable on Read the Docs.
    mock_imports=[
        "audiobiquad", "audiocore", "audioconvolve", "audiodelays",
        "audiodsp_util", "audiodynamics", "audioecho", "audiofilters",
        "audioladder", "audiomath", "audiomixer", "audiomodal", "audiopump",
        "audioroute", "audiosampler", "audioshaper", "audioverb",
        "synthio",
    ],
    # `rebuilt` only keeps old import paths alive.
    api_skip=["rebuilt"],
    version_file="../VERSION",
)

# docs/dev is not part of the site.
settings["exclude_patterns"].append("dev")

# Many docstrings in lib/ were written as Markdown, not reStructuredText, and
# docutils warns about the blocks it cannot parse. Fixing them is a change to
# the library's docstrings; until then the build tolerates them.
settings["suppress_warnings"] = ["docutils"]

globals().update(settings)

# index.md is plain Markdown so the docs read on GitHub too; the site
# navigation lives in contents.md.
master_doc = "contents"
