# B147 CPU ports and adaptive VRAM pressure

B147 layers one incremental patch on the accepted B146 build. The frozen branch
`best146-frozen-stability-hitches` stays at
`4d57a73f50bb1ea887c567c80c9d19bd5e94930c`.

## Changes

- Port chenxiao07/KytyPS5 `397112a0496fafb39f7fe9a2ed35868646ad9d43`:
  repeated guest shader writes keep their guest ordering without redundant image
  transitions; uploads, host work, layout and access changes still transition.
  Depth sampling retains read access when the sampled aspect is not writable.
  Draw packets count as work for global-barrier deduplication.
- Port `bdb81227f3a01174acbd9b0488844272921629ba`: relocated draw records distinguish
  mesh instances by descriptor identity after a rebind, retaining the occurrence
  fallback when descriptors themselves move.
- Include `222e53ef12822e04f9793226751346035370dad6`: retained descriptor sets check
  buffer object identity as well as image identity, and partial rebinding rejects
  other buffer slots whose objects are no longer live.
- Adapt shader hash memoization from upstream registration-generation reuse and
  the larger 8192-entry cache. The cache is allocated on the heap per thread;
  address, code size and registration generation are keys. Every 64 uses it
  rehashes all code bytes with the preserved B146 backing reader. A detected
  in-place change disables reuse for that entry until registration changes.
  Unregistered in-place patches can take up to 64 uses to be detected; use
  `run-hash-verify.cmd` for full-byte checking on every use.
- Already-retired image-pool allocations adapt their retained size to the current
  Vulkan memory budget. Under pressure, bounded LRU scanning retires at most eight
  sampled textures unused for 16 frames. Only CPU-backed, unmodified images qualify;
  storage/render/depth/video targets, metadata, GPU/stencil/buffer modifications
  and depth associations are excluded. Existing deferred GPU destruction remains.
  This cannot guarantee that an oversized active working set fits in VRAM.
- Driver checkpoints keep B146 snapshots, isolated optimizer cache, dirty-generation
  retry and atomic flushed writes. An identical successfully written payload skips
  another disk write; a missing file forces a rewrite. Slow checkpoints are logged.
- `FRAME-COSTS` reports exclusive recording-thread milliseconds averaged over
  60 flips: translation, texture preparation, pipeline work, GPU wait, upload wait
  and idle wait. Nested waits are subtracted from their parent categories. These
  are thread wall times, not whole-process CPU utilization or GPU utilization.

## Game compatibility and preservation

The ports operate on emulator resource state and introduce no title-specific guest
addresses, executable patch offsets, 01.007 shader seeds or game-version tests. The
candidate targets the same 01.004 installation as B146. Runtime compatibility and
FPS still require gameplay validation; results from another upstream GPU or game
revision are not a promise for this build.

The original source pin, ATRAC9 pin, indexed shader initialization, combined B123
performance patch, B127 reuse, B131 in-place preparation, guarded Windows fiber
stack/TLS/migration/termination fixes, cache keys, shader preparation settings,
settings window, audio and vblank behavior stay in the workflow. The clean-range
memory synchronization shortcut was already present in B146 and is retained.
`KYTY_VULKAN_RECORDING=0` and `KYTY_DEFERRED_SUBMIT=0` remain enforced.

The workflow applies B147 after B146. After compiling and running regressions, it
reverses B147 before checking the exact older patches, then restores every patch
before packaging. Existing checkpoint, texture-row and Windows fiber regressions
remain; new tests exercise hash invalidation/collisions, exclusive nested timing,
pressure arithmetic and ownership eligibility, extracted production image barriers,
instance occurrence/rebind gates and descriptor object lifetime.

## Launchers

`run.cmd` enables the new performance switches and frame costs. Existing
`run-verify.cmd` still compares native draw records with normal preparation.
`run-hash-verify.cmd` rehashes full code on every lookup.
`run-b146-comparison.cmd` disables instance identity, shader hash memoization, new
barrier reuse and adaptive pressure while keeping descriptor lifetime fixes,
checkpoint improvements and timing diagnostics. Use the frozen B146 artifact for
an exact older-binary comparison.

Local validation passed: new CPU/VRAM tests; extracted production barrier,
instance and descriptor lifetime tests; B146 checkpoint concurrency tests; texture
row-band tests; workflow structure and original launch-option preservation;
forward/reverse patch round trip; exact prior renderer patch checks. The Windows
workflow supplies full compilation and Windows-only fiber/render regressions.
