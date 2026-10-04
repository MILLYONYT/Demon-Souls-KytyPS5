"""Exercise the production dirty-row selection before enabling partial uploads."""
import argparse
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument("source", type=Path)
p.add_argument("output", type=Path)
a = p.parse_args()
text = (a.source / "src/graphics/host_gpu/renderer/cache/textureCache.cpp").read_text()
intersection = text[text.index("[[nodiscard]] bool IntersectsRanges("):text.index("// KYTY_PARTIAL_ROW_BANDS:")]
bands = text[text.index("struct RowBand {"):text.index("[[nodiscard]] uint64_t HashGuestRange(")]
a.output.write_text(r'''
#include <algorithm>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <utility>
#include <vector>
''' + intersection + bands + r'''
static void Check(bool value) { if (!value) std::abort(); }
int main() {
    uint32_t seed = 123;
    auto random = [&] { seed = seed * 1664525u + 1013904223u; return seed; };
    for (unsigned test = 0; test < 10000; ++test) {
        std::vector<std::pair<uint64_t, uint64_t>> raw, dirty;
        for (unsigned i = 0; i < test % 17; ++i) {
            const uint64_t start = random() % 6000;
            raw.emplace_back(start, start + 1 + random() % 300);
        }
        std::sort(raw.begin(), raw.end());
        for (const auto& range : raw) {
            if (!dirty.empty() && range.first <= dirty.back().second)
                dirty.back().second = std::max(dirty.back().second, range.second);
            else dirty.push_back(range);
        }
        std::vector<RowBand> selected;
        DirtyRowBands(dirty, 512, 4608, 256, 16, selected);
        uint32_t previous = 0;
        for (const auto& band : selected) {
            Check(band.first < band.last && band.last <= 16 && band.first >= previous);
            previous = band.last;
        }
        for (uint32_t row = 0; row < 16; ++row) {
            const uint64_t begin = 512 + row * 256, end = begin + 256;
            const bool expected = std::any_of(dirty.begin(), dirty.end(), [&](const auto& range) {
                return range.first < end && range.second > begin;
            });
            const bool actual = std::any_of(selected.begin(), selected.end(), [&](const RowBand& band) {
                return band.first <= row && row < band.last;
            });
            Check(expected == actual && IntersectsRanges(dirty, begin, end) == expected);
        }
    }
    // Exact boundaries are half-open; a neighbouring mip must not be uploaded.
    std::vector<std::pair<uint64_t, uint64_t>> dirty {{0, 512}, {768, 1024}, {4608, 4700}};
    std::vector<RowBand> selected;
    DirtyRowBands(dirty, 512, 4608, 256, 16, selected);
    Check(selected.size() == 1 && selected[0].first == 1 && selected[0].last == 2);
    std::puts("TextureRowBandTests: all cases passed");
}
''', encoding="utf-8")
