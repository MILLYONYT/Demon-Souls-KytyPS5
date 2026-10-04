"""Extract the patched production fiber switch for a quick host-only CI check.

The full emulator regression still runs later with its real memory subsystem.
This fixture uses committed host memory to catch ABI/TLS/stack-bound failures
before compiling the renderer and shader toolchain.
"""
import argparse
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("source", type=Path)
parser.add_argument("output", type=Path)
args = parser.parse_args()
kernel = (args.source / "src/libs/libKernel.cpp").read_text(encoding="utf-8")
start = kernel.index("namespace Fiber {")
end = kernel.index("} // namespace Fiber", start) + len("} // namespace Fiber")
fiber = kernel[start:end]
assert "FiberRestoreContextRaw" in fiber and "FIBER_STACK_EXTRA" in fiber
test = (args.source / "tests/FiberMigrationTests.cpp").read_text(encoding="utf-8")
test = "\n".join(line for line in test.splitlines() if not line.startswith('#include "'))
preamble = r'''
#include <algorithm>
#include <array>
#include <atomic>
#include <chrono>
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <mutex>
#include <semaphore>
#include <thread>
#include <unordered_map>
#define KYTY_SYSV_ABI __attribute__((sysv_abi))
#define KYTY_PLATFORM_WINDOWS 1
#if defined(_WIN32)
#define KYTY_PLATFORM KYTY_PLATFORM_WINDOWS
#define NOMINMAX
#include <windows.h>
#else
#define KYTY_PLATFORM 2
#include <sys/mman.h>
#endif
#define PRINT_NAME() ((void)0)
#define LOGF(...) ((void)0)
#define LIB_VERSION(...) static_assert(true)
#define EXIT(...) std::abort()
constexpr int OK = 0;
namespace Common {
void InitializeThreads() {}
struct Subsystems {
  template<class T> void Initialize() {}
  void Destroy() {}
};
}
namespace Config {
struct Lifecycle {};
enum class OutputDirection { Silent };
struct ConfigOptions { OutputDirection printf_direction; };
void Load(const ConfigOptions&) {}
}
namespace Log { struct Lifecycle {}; }
namespace Libs::LibKernel {
namespace Memory { struct Lifecycle {}; }
static std::mutex fixture_mutex;
static std::unordered_map<uint64_t, size_t> fixture_maps;
uint64_t MapGuestStack(size_t size) {
  const size_t committed = (size + 4095) & ~size_t(4095);
  const size_t total = committed + 4096;
#if KYTY_PLATFORM == KYTY_PLATFORM_WINDOWS
  auto* base = static_cast<uint8_t*>(VirtualAlloc(nullptr, total, MEM_RESERVE | MEM_COMMIT, PAGE_READWRITE));
  DWORD previous = 0;
  if (!base) return 0;
  if (!VirtualProtect(base, 4096, PAGE_NOACCESS, &previous)) {
    VirtualFree(base, 0, MEM_RELEASE);
    return 0;
  }
#else
  auto* base = static_cast<uint8_t*>(mmap(nullptr, total, PROT_READ | PROT_WRITE, MAP_PRIVATE | MAP_ANONYMOUS, -1, 0));
  if (base == MAP_FAILED) return 0;
  if (mprotect(base, 4096, PROT_NONE)) { munmap(base, total); return 0; }
#endif
  const auto stack = reinterpret_cast<uint64_t>(base + 4096);
  std::lock_guard lock(fixture_mutex);
  fixture_maps[stack] = total;
  return stack;
}
void UnmapGuestStack(uint64_t stack, size_t) {
  std::lock_guard lock(fixture_mutex);
  auto node = fixture_maps.extract(stack);
  if (!node) std::abort();
  auto* base = reinterpret_cast<void*>(stack - 4096);
#if KYTY_PLATFORM == KYTY_PLATFORM_WINDOWS
  if (!VirtualFree(base, 0, MEM_RELEASE)) std::abort();
#else
  if (munmap(base, node.mapped())) std::abort();
#endif
}
}
'''
args.output.parent.mkdir(parents=True, exist_ok=True)
args.output.write_text(preamble + "\nnamespace Libs {\n" + fiber + "\n}\n" + test + "\n", encoding="utf-8")
print("Generated preflight from the patched production fiber code and migration regression.")
