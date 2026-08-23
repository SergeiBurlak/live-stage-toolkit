# ShowNet — deterministic Art-Net output for Unreal Engine

Sending DMX from the game thread means a render hitch becomes a lighting failure
in front of an audience. This subsystem moves show output onto an isolated
thread so that the two are never coupled.

## What it does

- Fixed-rate Art-Net output at up to 44 Hz, the physical maximum for DMX512,
  scheduled independently of frame rate.
- Double-buffered channel data guarded by a critical section, so the game thread
  can write at any time without blocking output.
- A watchdog: if the game thread stops calling `KeepAlive()` for longer than the
  configured timeout, every universe is driven to zero. A frozen engine goes to
  blackout rather than holding the last frame.
- A latched emergency stop callable from Blueprint.
- Three blackout frames on shutdown, so no fixture can latch on a stale value.
- Runtime statistics: packets sent, send errors, worst loop interval, time since
  the last keep-alive.

## Installation

This requires a C++ project. In a Blueprint-only project, use
`File > New C++ Class` once to add C++ support, then place these files in your
project's `Source/<YourModule>/` directory.

Add the dependencies to your module's `Build.cs`:

    PublicDependencyModuleNames.AddRange(new string[] {
        "Core", "CoreUObject", "Engine", "Sockets", "Networking"
    });

Rebuild the project.

## Usage from Blueprint

Get the subsystem from the Game Instance, then:

    Configure("2.0.0.255", 6454, 44.0, 250.0)
    RegisterUniverse(0)
    SetChannel(0, 1, 255)        // universe 0, channel 1, full
    KeepAlive()                  // call every tick from your show controller

`Configure` takes the target address, the Art-Net port, the refresh rate in hertz
and the watchdog timeout in milliseconds. Use a directed broadcast address such
as `2.0.0.255`, or the unicast address of a specific node.

`KeepAlive()` must be called every frame. It is the mechanism by which the sender
thread knows the engine is still alive.

## Verifying it

Run `tools/artnet_probe.py` from this repository on the receiving machine. It
will report the actual refresh rate, dropped frames and jitter percentiles.

## Licence

MIT.
