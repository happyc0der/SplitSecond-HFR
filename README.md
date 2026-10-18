# Split/Second HFR — native 60 FPS for Split/Second (PC)

Split/Second (Black Rock Studio, 2010) is locked to 30 FPS on PC, and simply removing the cap makes the game run
at the wrong speed and breaks its physics. This mod makes the game run a **real 60 Hz game loop** instead — it is
not frame interpolation — while keeping the game's speed and physics exactly as designed.

> **This fork** adds support for the **community DLC build** of the game: the `SplitSecond.exe` that ships with the
> Xbox 360 DLC port (built 11 May 2010, TimeDateStamp `0x4BE94A54`). Upstream only supports the Steam exe, and the DLC
> data doesn't run with the Steam exe, so anyone using the DLC tracks and cars had no 60 FPS. The mod now picks a
> per-build address profile at start-up; the Steam build behaves exactly as upstream. See
> [The DLC build](#the-dlc-build-this-fork) below. Upstream: [preseznik/SplitSecond-HFR](https://github.com/preseznik/SplitSecond-HFR).

## What it does

- **Native 60 FPS.** Internally the game already simulates physics in fixed 1/60 s steps; at 30 FPS it just runs two
  of them per frame. The mod changes the frame limiter so it runs one step per 1/60 s frame. Everything that counts
  those steps keeps its real-time speed, and the car physics are identical to the original.
- **Precise frame pacing.** The game's limiter sleeps in whole milliseconds; the mod waits for the exact deadline.
- **AI fix.** The AI drivers' steering controller is tuned per frame, so they keep making decisions at their
  original 30 Hz rate and drive exactly as in the original game.
- **F8** switches between 30 and 60 FPS while playing.
- **Nothing on disk is modified** and the game's copy protection is left untouched: the game itself loads the mod
  at start-up (it looks for a debugging library called `DXFreezerServer.dll` in its folder).

## Status

Version 0.1.3 — early release. Verified: steady 60 FPS, physics and handling, game speed, live 30 ↔ 60 switching.
Not yet verified at 60 FPS: every Power Play (especially multi-stage ones), shortcut doors and ramps, all tracks.
Please report anything that behaves differently at 60 than at 30 (F8 makes comparing easy).

For 120 Hz displays: run the mod at 60 FPS and add frame generation on top (e.g. Lossless Scaling ×2), or use VRR.

## Requirements

- The **Steam version** of Split/Second (`SplitSecond.exe` 1.0.0.1), or the **DLC build** described below (this
  fork). Other executables (retail discs, patched or "unpacked" exes) are detected and the mod stays inactive.
- Windows 10 or 11. Linux / Steam Deck via Proton works too (see below).

## Install

1. Download `SplitSecond-HFR-v0.1.3-dlc1.zip` from the [Releases](../../releases) page.
2. Copy `DXFreezerServer.dll`, `DXFreezerServer_d.dll` and `SplitSecondHFR.ini` into the game folder
   (Steam → right-click Split/Second → Manage → Browse local files). The two DLLs are the same file: the Steam exe
   loads the first name, the DLC build the second.
3. Start the game. `hfr_logs\<date-time>\hfr.log` names the build it found
   (`Profile: Steam 1.0.0.1` or `Profile: DLC build (11-May-2010)`).

To uninstall, delete those three files (and the `hfr_logs` folder the mod creates).

## Configuration (`SplitSecondHFR.ini`)

| Option | Default | Meaning |
|---|---|---|
| `[General] Enabled` | 1 | 0 = the mod changes nothing (handy for comparing with the original game) |
| `[Timing] Mode` | 60 | 60 = native 60 Hz; 30 = original behaviour |
| `[Timing] PreciseLimiter` | 1 | exact frame pacing (automatically off under Wine/Proton); 2 = force on (not recommended under Proton); 0 = off |
| `[Fixes] AI30Hz` | 1 | AI decisions at their original 30 Hz rate |
| `[Hotkeys] ToggleFps` | 0x77 (F8) | key that switches 30 ↔ 60; 0 disables it |
| `[Hotkeys] Marker` | 0 | key that writes a `MARKER` line into the log (e.g. 0x79 = F10), to note when something happened |
| `[Logging] FrameLog` | 0 | 1 = also write per-frame timings (`frames.csv`) |
| `[Logging] MemoryLog` | 0 | 1 = log the game's memory use every `MemoryLogSec` seconds (default 10), even with `Enabled=0` |

## Logs and troubleshooting

Each session writes `hfr_logs\<date-time>\hfr.log` in the game folder: the version check, the active mode and an
FPS summary every 5 seconds. If something looks wrong, set `Enabled=0` to check whether the original game does the
same, and include the log when reporting an issue.

## Linux / Steam Deck (Proton)

The mod works under Proton. Precise frame pacing is switched off automatically there (the log says
`Wine/Proton detected - precise pacing disabled`), because it crashed at the main menu with Proton-CachyOS 11 and
ntsync and hung with Proton 10 + fsync; the game's own pacing is smooth at 60 FPS under Proton anyway.
`PreciseLimiter=2` forces it back on, which is not recommended under Proton.

## Building from source

Requires Visual Studio 2022 (MSVC x86 toolset) and CMake ≥ 3.25.

```
cmake -S . -B build -G "Visual Studio 17 2022" -A Win32
cmake --build build --config Release
```

`cmake --build build --config Release --target deploy` copies the DLL (and the INI, if none is present) into the
game folder; set `-DGAME_DIR=...` when configuring if the game is not in the default Steam location.

## How it works

The game's main loop (`0x558880`) accumulates measured frame time and calls `Update(ticks)` once per 1/30 s with two
ticks of 1/60 s. The mod redirects the loop's three reads of the 1/30 s period to its own 1/60 s value and changes
the "2 ticks" constants to 1 — five small in-memory changes, each checked against the expected original bytes before
it is written and reverted when switching back to 30. Physics are stepped once per tick, so they run exactly as
before. The AI driver update is gated to every second tick via a pointer swap in its virtual table.

## The DLC build (this fork)

The DLC port's exe is a different compile of the game (May 2010, SecuROM-wrapped, so the first ~3 MB of its code is
encrypted on disk and only readable at runtime). The game logic is the same, but every address moved, and a few
details changed. The addresses were mapped from runtime memory dumps of both builds, matching the code
instruction by instruction:

| What | Steam 1.0.0.1 | DLC build |
|---|---|---|
| TimeDateStamp | `0x4BE13C66` | `0x4BE94A54` |
| Debug-hook loader / DLL name | `DXFreezerServer.dll` | `0x89F140`, loads `DXFreezerServer_d.dll` |
| Frame-limiter tick function | `0x558880` | `0x558910` |
| "2 ticks" after the sleep | immediate `2` | read from a variable that holds 2 (`mov esi,[0xD156A0]`), patched to `mov esi,1` |
| AI update (vtable slot 3 of `cAIPlayer`) | upstream value | vtable `0xBC0C1C`, slot `0xBC0C28` → `0x51AA10` |
| IAT: GetTickCount / WaitForMultipleObjects / timeGetTime | upstream values | `0xB9B164` / `0xB9B1CC` / `0xB9B2D0` |

The values live in `kDlcProfile` (`src/core/version_gate.cpp`); every patch is still checked against the expected
original bytes before it's written. One behavioural difference: the DLC build's loader **dereferences** the value
returned by `dxfreezer_Direct3DCreate9` (`mov [0xD8584C],eax; mov eax,[eax]`), so on that build the hook returns a
small holder `{IDirect3D9*, 0, stand-in object}`. The game's debug helpers call the stand-in, which returns `S_OK`.
Returning the bare `IDirect3D9*` crashes in the NVIDIA driver at start-up.

Tested on the DLC build: a 19-minute play session held 60.0 FPS in 209 of its 211 five-second windows (the other two
were loading). Not every track and Power Play has been checked at 60 yet.

Related: [SplitSecond-PadFix](https://github.com/happyc0der/SplitSecond-PadFix) (Bluetooth Xbox controllers) and
[SplitSecond-ButtonNames](https://github.com/happyc0der/SplitSecond-ButtonNames) (Xbox button names in prompts).

## License and credits

- The mod's source code is licensed under the **GNU General Public License v3.0** (see `LICENSE`).
- Bundled: [SafetyHook](https://github.com/cursey/safetyhook) (Boost Software License 1.0) and
  [Zydis](https://github.com/zyantific/zydis) (MIT) in `third_party/`.
- This is an unofficial fan project, not affiliated with Disney or Black Rock Studio. Split/Second is a trademark of
  its respective owner. You need your own copy of the game.
