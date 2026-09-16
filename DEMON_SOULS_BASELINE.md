# Demon’s Souls baseline

The preferred Windows build for Demon’s Souls is **KytyPS5 Build 32 LTO BEST**. Treat this build as the behavioral baseline for future Demon’s Souls work. Newer build numbers, including Build 52, do not supersede it without comparison against this baseline.

## Baseline archive

- Filename: `KytyPS5-Build32-LTO-BEST.zip` (uploaded copies `(1)` and `(3)` are byte-for-byte identical)
- SHA-256: `b4c9aad01b22886beef0dda58d1978b8acfc5fe39577ed1a348fd34abc502dea`
- Format: Windows binaries and dependencies, including `kyty_emulator.exe` and `launcher.exe`
- Archive integrity: all 60 entries passed ZIP integrity checks

This repository's current `main` source tree is not proven to reproduce the archived executable. Do not infer the source commit from the ZIP timestamps. Keep this binary as the comparison build; identify matching source separately before treating source changes as improvements over Build 32.

The archive must be attached to a GitHub Release separately. This note does not contain or publish the binary.
