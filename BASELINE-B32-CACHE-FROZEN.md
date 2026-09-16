# Frozen Windows Build 32 baseline: Vulkan cache enabled

User-tested baseline accepted on 2026-09-16. Keep this checkpoint unchanged; create separate branches for subsequent performance and crash fixes. This is a Windows x64 test build, not a release. No macOS or Linux jobs.

## Verified artifact

- Original baseline input ZIP SHA-256: `b4c9aad01b22886beef0dda58d1978b8acfc5fe39577ed1a348fd34abc502dea`
- Cache-enabled Windows x64 ZIP SHA-256: `20505da485451cf895c6eed58c9c44b6fc127f36d4bee4c28cb09a33026c5569`
- `kyty_emulator.exe` SHA-256: `342de180bd76ef1d31a4990b9d7ba042d5d007aa164fc7b86c7284d278ecac26`
- `launcher.exe` SHA-256: `615965e4df37b5eb8249e7d998a0750f636185a66b245dd59e042f6f1378c89c`
- Successful GitHub Actions run: https://github.com/MILLYONYT/Demon-Souls-KytyPS5/actions/runs/35148246737
- Artifact name: `DemonSouls-B32-CACHE-TEST-Windows-x64-3`; artifact ID: `10468985860`. Actions artifacts expire; preserve the ZIP independently.
- Build recipe commit: `a7244478db184a141f6383d7825509c6e8d29abf`
- Recovered source revision: `fbcc0c6914a9e76ae5dc52358b935657dcfcb7d7`
- Cache and Windows compilation patch: `patches/enable-vulkan-cache.patch`
- Build workflow: `.github/workflows/b32-cache-source-test.yml`

## Observed runtime behavior

A fresh run reported `Vulkan pipeline cache: initialized empty`. A subsequent playthrough reported `Vulkan pipeline cache: loaded 74680589 bytes from _PipelineCache\\PPSA01342.bin`, then launched without a crash. The user confirmed the build was playing perfectly at this checkpoint.

The exact uncommitted edits in the original `fbcc0c6-dirty` binary were not available from its archive. The cache-enabled executable is a rebuilt candidate; the hashes above define the exact user-tested checkpoint.

Future changes should branch from the frozen branch and produce a separate Windows-only test artifact. Do not overwrite this ZIP or change the frozen branch.
