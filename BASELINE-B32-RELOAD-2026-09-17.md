# Current main Build 32 Windows testing baseline (2026-09-17)

This is the user-selected frozen build from Windows-only test run [35171797267](https://github.com/MILLYONYT/Demon-Souls-KytyPS5/actions/runs/35171797267). Keep this branch fixed; make subsequent fixes on a separate Windows testing branch. It is a test artifact, not a release.

- Recipe commit: `a3386a77d4d583ce8c0707bb57480649f8408f49`
- Source revision: `fbcc0c6914a9e76ae5dc52358b935657dcfcb7d7`, with `patches/enable-vulkan-cache.patch`
- Artifact: `DemonSouls-B32-CRASH-TEST-Windows-x64-11` (ID `10477117405`; GitHub Actions artifact expires)
- ZIP SHA-256: `ff3a5ee065161b0183d1c67bffaefaefb921b0fbff04d75e7bd4af95cf86e2a1`
- `kyty_emulator.exe` SHA-256: `4a002ef8b0ac6b800912617fd996adf04167cc8c74a7ef4f665a9d4d9a07a3ea`
- `launcher.exe` SHA-256: `f10143d81618f8b5322960fbf26043f2b1fea60b80ec9e51be4886718006c75e`

Known remaining issue: after save/quit, reload, save/quit, and start new game, shader `stage=4 hash=0xb3ee9eea5b92b870` failed with `a descriptor source did not evaluate`. Earlier shader `0x05021f35c669b111` logged unavailable indirect table and fallback. This checkpoint was requested despite the known reload crash.

This repository branch contains the reproducible build recipe; `main` source files themselves are not the compiled source tree. The Windows workflow checks out the source revision above, applies the patch, and creates the Windows x64 artifact. No macOS/Linux test artifacts or release are part of this baseline.
