# B146 frozen baseline

The user accepted the successful B146 build and requested it be frozen as the new base.

- Exact packaging commit: `4d57a73f50bb1ea887c567c80c9d19bd5e94930c`
- Frozen branch: [best146-frozen-stability-hitches](https://github.com/MILLYONYT/Demon-Souls-KytyPS5/tree/best146-frozen-stability-hitches)
- Successful Windows build: [37168895686](https://github.com/MILLYONYT/Demon-Souls-KytyPS5/actions/runs/37168895686)
- Artifact: `KytyPS5-B146-STABILITY-HITCHES-Windows-x64-146`
- Artifact SHA-256: `b0dfba5765123f6b5b6b66bcc071295926f53be379f18a9b49d501f07f3be22b`

Use this frozen commit as the base for subsequent work. Keep all existing FPS, rendering, shader/cache, settings and crash-protection patches. The pinned public source, audio dependency and cache identity are unchanged. The full workflow and its embedded fixes remain available at the frozen commit.

The frozen branch identifies the exact successful build; leave it at that commit. Continue changes on `best132-shader-precompile-settings`. This baseline registration changes documentation only and does not rebuild or alter emulator code. GitHub's current artifact expires on 2027-01-02T01:43:51Z; the frozen source/workflow remains reproducible.

See [b146-frozen-baseline.json](b146-frozen-baseline.json) for the machine-readable build and preservation record. Build success is recorded here; gameplay confirmation remains a separate test result.
