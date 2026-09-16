# Demon’s Souls baseline

The preferred Windows build for Demon’s Souls is **KytyPS5 Build 32 LTO BEST**. Treat this build as the behavioral baseline for future Demon’s Souls work. Newer build numbers, including Build 52, do not supersede it without comparison against this baseline.

## Baseline archive

- Filename: `KytyPS5-Build32-LTO-BEST.zip` (uploaded copies `(1)` and `(3)` are byte-for-byte identical)
- SHA-256: `b4c9aad01b22886beef0dda58d1978b8acfc5fe39577ed1a348fd34abc502dea`
- Format: Windows binaries and dependencies, including `kyty_emulator.exe` and `launcher.exe`
- Archive integrity: all 60 entries passed ZIP integrity checks

This repository's current `main` source tree is not proven to reproduce the archived executable. Do not infer the source commit from the ZIP timestamps. Keep this binary as the comparison build; identify matching source separately before treating source changes as improvements over Build 32.

The exact archive is published as the [Build 32 LTO BEST release](https://github.com/MILLYONYT/Demon-Souls-KytyPS5/releases/tag/DemonSoulsKytyPS5). Its executable identifies itself as `fbcc0c6-dirty`; that source revision and its uncommitted changes are unavailable here. The [verified baseline workflow](https://github.com/MILLYONYT/Demon-Souls-KytyPS5/actions/workflows/best-baseline.yml) copies the release asset and checks its hash, while `tools/build_from_best.py` can prepare guarded byte-patch experiments.
