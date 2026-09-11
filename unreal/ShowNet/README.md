# ShowNet — deterministic Art-Net output for Unreal Engine

Sending DMX from the game thread means a render hitch becomes a lighting failure
in front of an audience. This subsystem moves show output onto an isolated
thread so that the two are never coupled.

## What it does

- Fixed-rate Art-Net output at up to 44 Hz, the physical maximum for DMX512,
  scheduled independently of frame rate.
- Double-buffered channel data guarded by a critical section, so the game thread
  can write at any time without blocking output. The sender thread copies each
  frame's data out under that lock and releases it before touching the socket,
  so a slow or blocked send can never stall a game-thread write.
- A watchdog: if the game thread stops calling `KeepAlive()` for longer than the
  configured timeout, every universe is driven to zero. A frozen engine goes to
  blackout rather than holding the last frame.
- A latched emergency stop callable from Blueprint.
- Three blackout frames on shutdown, so no fixture can latch on a stale value.
- Runtime statistics: packets sent, send errors, worst loop interval, time since
  the last keep-alive.

## Two things that are easy to get wrong

**`KeepAlive()` must come from a real per-frame source.** Call it from `Event
Tick`, or from a dedicated repeating timer at a high rate (10–20 Hz or more) -
never from a sequential `Delay` chain. This project's only proven Blueprint
trigger pattern (`BP_ConfettiConductor`) is built on `Delay` nodes, which can
fire seconds apart. If `KeepAlive()` is wired the same way, the watchdog will
see gaps far longer than its timeout between calls and will force every
universe to blackout between each `Delay` firing - lights will flicker to
black continuously even though nothing has actually frozen.

**`Configure()` silently clears an active `EmergencyStop()`.** Calling
`Configure()` again - to change the target address, refresh rate, or simply
because a show-controller `BeginPlay` calls it defensively - replaces the
sender and releases any latched stop, without an explicit
`ClearEmergencyStop()`. This is intentional (a reconfigure is treated as a
fresh start), but it means `EmergencyStop()` is not a substitute for
physically confirming the rig is safe before `Configure()` runs again
mid-show. The engine logs a `Warning` to `LogShowNet` whenever this happens,
so it is visible in the Output Log rather than silent - watch for it.

The watchdog timeout is floored at 100 ms for the same reason as the first
point above: a typical 30 fps game thread ticks every ~33 ms, so a lower
value risks tripping the watchdog on ordinary frame-time variance. If you
need tighter margins, confirm `KeepAlive()` is Tick-driven first.

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
    KeepAlive()                  // call every Tick from your show controller

`Configure` takes the target address, the Art-Net port, the refresh rate in hertz
and the watchdog timeout in milliseconds. Use a directed broadcast address such
as `2.0.0.255`, or the unicast address of a specific node.

`KeepAlive()` must be called every frame. It is the mechanism by which the sender
thread knows the engine is still alive. See "Two things that are easy to get
wrong" above before wiring this into a Blueprint that also drives show content.

## Verifying it

Run `tools/artnet_probe.py` from this repository on the receiving machine. It
will report the actual refresh rate, dropped frames, sender restarts and
jitter percentiles.

## Licence

MIT.
