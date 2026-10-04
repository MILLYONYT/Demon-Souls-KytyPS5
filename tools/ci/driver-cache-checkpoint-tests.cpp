#include "driver-cache-checkpoint.h"

#include <cstdio>
#include <cstdlib>
#include <future>
#include <memory>
#include <semaphore>
#include <stdexcept>
#include <vector>

using namespace std::chrono_literals;
static void Check(bool value, const char* message) {
    if (!value) { std::fprintf(stderr, "CheckpointTests: %s\n", message); std::abort(); }
}
template<class Predicate> static void Await(Predicate ready) {
    const auto deadline = std::chrono::steady_clock::now() + 5s;
    while (!ready()) {
        Check(std::chrono::steady_clock::now() < deadline, "timed out");
        std::this_thread::sleep_for(1ms);
    }
}
int main() {
    // Idle caches never write. Failed writes and exceptions retain dirty state.
    {
        std::atomic<unsigned> calls {0};
        DriverCacheCheckpoint saver([&] {
            const auto call = ++calls;
            if (call == 1) throw std::runtime_error("simulated allocation failure");
            return call >= 3;
        }, 5ms);
        std::this_thread::sleep_for(25ms);
        Check(calls == 0, "clean cache wrote to disk");
        saver.MarkDirty();
        Await([&] { return calls >= 3; });
        std::this_thread::sleep_for(25ms);
        Check(calls == 3, "successful generation was written again");
        saver.Stop(); saver.Stop();
    }
    // A pipeline completed during a snapshot must not be lost by that snapshot.
    {
        std::atomic<unsigned> calls {0};
        std::binary_semaphore entered(0), release(0);
        DriverCacheCheckpoint saver([&] {
            if (++calls == 1) { entered.release(); release.acquire(); }
            return true;
        }, 5ms);
        saver.MarkDirty();
        Check(entered.try_acquire_for(5s), "first snapshot never started");
        std::vector<std::thread> producers;
        for (unsigned i = 0; i < 8; ++i) producers.emplace_back([&] {
            for (unsigned j = 0; j < 100; ++j) saver.MarkDirty();
        });
        for (auto& producer : producers) producer.join();
        release.release();
        Await([&] { return calls >= 2; });
        saver.Stop();
        Check(calls == 2, "concurrent changes were lost or repeatedly saved");
    }
    // Shutdown joins an active snapshot before Vulkan caches can be destroyed.
    {
        std::binary_semaphore entered(0), release(0);
        std::atomic<bool> completed {false};
        DriverCacheCheckpoint saver([&] {
            entered.release(); release.acquire(); completed = true; return true;
        }, 5ms);
        saver.MarkDirty();
        Check(entered.try_acquire_for(5s), "shutdown snapshot never started");
        auto stopped = std::async(std::launch::async, [&] { saver.Stop(); });
        Check(stopped.wait_for(20ms) == std::future_status::timeout, "shutdown did not join active snapshot");
        release.release();
        Check(stopped.wait_for(5s) == std::future_status::ready && completed, "snapshot outlived shutdown");
        stopped.get();
    }
    // Cancel a long interval promptly; destructor must not wait ten seconds.
    {
        auto saver = std::make_unique<DriverCacheCheckpoint>([] { return true; }, 10s);
        const auto start = std::chrono::steady_clock::now();
        saver.reset();
        Check(std::chrono::steady_clock::now() - start < 1s, "idle shutdown blocked on timer");
    }
    std::puts("CheckpointTests: all cases passed");
}
