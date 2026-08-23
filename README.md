Live Stage Toolkit

Open engineering tools for building real-time markerless motion capture and show
output systems for live theatre with Unreal Engine 5.

These tools were written for Queen Anne, a theatre production in which live
dancers drive digital performers rendered in real time and projected on stage.
They are published because independent theatres should not have to rediscover
this knowledge one failure at a time.

Why this exists

Markerless motion capture works well in a studio. A theatre is not a studio.
The stage is dark, the lights flicker, the fixtures change colour every few
seconds, and the performers move fast. Most of the questions that decide whether
such a system works at all are answerable with arithmetic, before any money is
spent:

How many cameras, at what focal length, at what height?
How many pixels of body height does that give at the far corner of the stage?
How short must the exposure be to avoid motion blur, and how much light does that demand?
Will the camera streams fit down the network?
How bright will the projected image actually be on that surface?
How much latency will the audience see?

This toolkit answers those questions numerically, and provides the runtime
components needed to output a show safely.

Tools
tools/stage_rig_calculator.py

Computes the full engineering budget of a stage capture and projection system.
No dependencies beyond the Python standard library.

Sample output for a 5 x 5 m capture zone with 5 MP global-shutter cameras:

Distance near / centre / far ......... 3.57 / 5.50 / 9.18 m
Required horizontal FOV .............. 70.5 degrees
Recommended focal length ............. 6.0 mm
Body height in pixels, far point ..... 339 px
Maximum exposure for 2 px blur ....... 1.76 ms
Required scene illuminance ........... 64 lux
Per-camera network load .............. 2.406 Gbit/s
End-to-end latency ................... 187.7 ms

Run it:

python3 stage_rig_calculator.py --width 7 --depth 6 --rig-height 4.5 \
    --performers 4 --cameras 6 --preset imx250 --fps 60

Self-test:

python3 stage_rig_calculator.py --selftest
tools/artnet_probe.py

Show-network quality assurance. Listens on UDP 6454, decodes Art-Net DMX packets
and reports, per universe: effective refresh rate, dropped frames detected from
the sequence field, duplicates, out-of-order packets, and inter-packet interval
percentiles.

Intended to be run before every rehearsal. If the 99th percentile interval
exceeds one and a half DMX frames, fixtures will visibly stutter.

python3 artnet_probe.py --seconds 30 --nominal-hz 44
unreal/ShowNet/

An Unreal Engine subsystem for deterministic Art-Net output. Sending DMX from the
game thread means a render hitch becomes a lighting failure in front of an
audience. This component moves output to an isolated thread at a fixed rate, with
double-buffered channel data, a watchdog that blacks out every universe if the
game thread stalls, a latched emergency stop, and three blackout frames on
shutdown so no fixture can latch on a stale value.

Findings worth knowing before you buy anything

Use global-shutter sensors. LED stage fixtures dim by pulse-width modulation
at hundreds to thousands of hertz. A rolling-shutter sensor exposes each row at a
different phase of that cycle and records banding. A global shutter exposes every
pixel at once, so the mechanism that produces banding does not exist.

Light in the near infrared. At a realistic dance hand speed of 6 m/s, keeping
motion blur under two pixels caps exposure at roughly 1.76 ms, which demands far
more light than a dark stage provides. Infrared illumination at 850 nm with
bandpass filters on the lenses removes stage lighting from the capture path
entirely. The lighting designer regains full freedom.

Synchronise in hardware. A 5 ms desynchronisation between cameras displaces a
hand moving at 6 m/s by 30 mm, which is enough to break triangulation. Hardware
genlock reduces the error to fractions of a millimetre. Software frame alignment
does not.

Check the network before choosing cameras. A 5 MP monochrome sensor at 60 fps
produces 2.4 Gbit/s. That does not fit a gigabit link. Either the resolution, the
frame rate, or the interface has to change, and it is cheaper to discover this
with a calculator than with a purchase order.

Status

Early. Tools are used in production on the project they were written for. The
calculator and the probe include self-tests. Issues and pull requests welcome.

Licence

MIT. Use it, change it, ship it.

[Русская версия](README.ru.md)
