# Public performance candidate — bb0fbe7
Start with run.cmd and select the folder containing eboot.bin. The supported game is PPSA01341 / 01.007.000.
Extract to a NEW folder. Keep #112 and its caches and saves as your comparison build.
If transferring a save, COPY your backed-up _SaveData folder; never move or delete the baseline.

## What changed
Pinned public source: https://github.com/chenxiao07/KytyPS5/tree/bb0fbe7e9f22d9bf2455f486fbf1a9aa33a6354d
The branch implements native XPR draw preparation, a Vulkan recording worker and deferred submission,
independent readback transfers, partial texture uploads, asynchronous pipeline optimization,
and October 1 low-VRAM garbage-collection fixes. This package enables the documented runtime
performance paths. It reconstructs their switch configuration; the author's private launch.json,
PGO profile, SRT AOT DLL and shader recordings are unavailable.

The author reports approximately 35–40+ FPS in test scenes on i9-14900K / RTX 5090.
Their 8 GB VRAM experiment limits a 5090's memory budget; it is NOT an RTX 4060 benchmark.
This build is a candidate for replacing #112 only after your same-scene test. FPS is not guaranteed.
The #112 frozen branch retains its exact source and all 28 patches. The candidate uses the
author's broader source architecture rather than applying those older overlapping patches blindly.

## Shader stalls
The executable includes quick initial pipeline builds with background optimization.
For comprehensive offline preparation, install Python 3.11+ and NumPy:
    python -m pip install numpy
Choose the game once with run.cmd, close it, then run precompile.cmd. It extracts shader seeds
from YOUR installed game and compiles them for YOUR GPU/driver. It can take an hour or more.
No game files, shader seeds, saves, proprietary Streamline binaries, PGO profile or AOT DLL are shipped.
Existing #112 caches remain in the baseline folder. New source/code generation may need new shaders;
do not delete the old cache.

## Test
Use the same save, location and camera as #112. Let the background preparation finish before measuring.
Report steady FPS, walking stalls, texture flicker, and newest logs/*.out.log and *.err.log.
A 1080p window affects presentation size and does not establish that the game's internal rendering is 1080p.
Native game FPS is the comparison metric; frame generation is disabled.
