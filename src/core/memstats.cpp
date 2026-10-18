// Address-space / memory statistics for the 32-bit game: 2 GB of user address space, or 4 GB on 64-bit Windows when
// the exe has the large-address-aware flag set (the DLC build's bigger data can exhaust 2 GB in a long session).
// Passive (VirtualQuery only): used address space (reserved + committed), largest free block, private commit.
// [Logging] MemoryLog=1 logs it periodically, even with Enabled=0.
#include "common.h"

#include <psapi.h>

namespace hfr {

void LogMemoryStats() {
    uint64_t used = 0, committed = 0, largestFree = 0, freeTotal = 0;
    SYSTEM_INFO si;
    GetSystemInfo(&si);
    const uintptr_t top = reinterpret_cast<uintptr_t>(si.lpMaximumApplicationAddress);
    MEMORY_BASIC_INFORMATION mbi;
    for (uintptr_t a = 0x10000; a < top;) {
        if (!VirtualQuery(reinterpret_cast<void*>(a), &mbi, sizeof(mbi))) break;
        uint64_t size = mbi.RegionSize;
        if (mbi.State == MEM_FREE) {
            freeTotal += size;
            if (size > largestFree) largestFree = size;
        } else {
            used += size;
            if (mbi.State == MEM_COMMIT) committed += size;
        }
        uintptr_t next = reinterpret_cast<uintptr_t>(mbi.BaseAddress) + mbi.RegionSize;
        if (next <= a) break;
        a = next;
    }
    PROCESS_MEMORY_COUNTERS_EX pmc{};
    pmc.cb = sizeof(pmc);
    GetProcessMemoryInfo(GetCurrentProcess(), reinterpret_cast<PROCESS_MEMORY_COUNTERS*>(&pmc), sizeof(pmc));
    Log("memory: address space used %.0f MB of %.0f (committed %.0f MB), free %.0f MB, largest free block %.0f MB, "
        "private %.0f MB",
        used / 1048576.0, (top + 1.0) / 1048576.0, committed / 1048576.0, freeTotal / 1048576.0, largestFree / 1048576.0,
        pmc.PrivateUsage / 1048576.0);
}

namespace {
DWORD WINAPI MemoryLogThread(void*) {
    for (;;) {
        LogMemoryStats();
        Sleep(static_cast<DWORD>(g_cfg.memoryLogSec) * 1000);
    }
}
} // namespace

void StartMemoryLog() {
    HANDLE h = CreateThread(nullptr, 0, MemoryLogThread, nullptr, 0, nullptr);
    if (h) CloseHandle(h);
}

} // namespace hfr
