#!/usr/bin/env python3
"""
artnet_probe.py - Art-Net show network quality assurance.

Listens on UDP 6454, decodes ArtDmx packets and reports, per universe:

  * effective refresh rate in hertz
  * dropped frames, detected from the Art-Net sequence field
  * inter-packet interval statistics (mean, p50, p95, p99, max)
  * out-of-order and duplicate packets

Run it on the lighting VLAN before every rehearsal. If the 99th percentile
interval exceeds roughly one and a half times the nominal DMX period
(22.7 ms at 44 Hz), fixtures will visibly stutter.

No dependencies beyond the Python standard library.

Part of the Live Stage Toolkit. MIT licence.

Usage
-----
    python3 artnet_probe.py --bind 0.0.0.0 --seconds 30
    python3 artnet_probe.py --seconds 60 --json report.json
    python3 artnet_probe.py --selftest
"""

from __future__ import annotations

import argparse
import json
import socket
import statistics
import struct
import sys
import threading
import time
from dataclasses import dataclass, field

ARTNET_PORT = 6454
ARTNET_ID = b"Art-Net\x00"
OP_DMX = 0x5000
OP_POLL = 0x2000
OP_POLL_REPLY = 0x2100
OP_SYNC = 0x5200


@dataclass
class UniverseStats:
    port_address: int
    packets: int = 0
    dropped: int = 0
    out_of_order: int = 0
    duplicates: int = 0
    last_sequence: int | None = None
    last_timestamp: float | None = None
    intervals: list[float] = field(default_factory=list)
    first_timestamp: float | None = None
    max_channel_seen: int = 0

    def observe(self, sequence: int, length: int, timestamp: float) -> None:
        self.packets += 1
        self.max_channel_seen = max(self.max_channel_seen, length)

        if self.first_timestamp is None:
            self.first_timestamp = timestamp
        if self.last_timestamp is not None:
            self.intervals.append((timestamp - self.last_timestamp) * 1000.0)
        self.last_timestamp = timestamp

        # Sequence 0 means the sender disabled sequencing; skip loss detection.
        if sequence == 0:
            self.last_sequence = 0
            return

        if self.last_sequence is None or self.last_sequence == 0:
            self.last_sequence = sequence
            return

        expected = 1 if self.last_sequence == 255 else self.last_sequence + 1
        if sequence == expected:
            pass
        elif sequence == self.last_sequence:
            self.duplicates += 1
        else:
            gap = (sequence - expected) % 256
            if gap > 128:
                self.out_of_order += 1
            else:
                self.dropped += gap
        self.last_sequence = sequence

    def summary(self) -> dict:
        span = 0.0
        if self.first_timestamp is not None and self.last_timestamp is not None:
            span = self.last_timestamp - self.first_timestamp
        hz = (self.packets - 1) / span if span > 0 else 0.0
        data = {
            "universe": self.port_address,
            "net": (self.port_address >> 8) & 0x7F,
            "subuni": self.port_address & 0xFF,
            "packets": self.packets,
            "hz": round(hz, 2),
            "dropped": self.dropped,
            "duplicates": self.duplicates,
            "out_of_order": self.out_of_order,
            "channels": self.max_channel_seen,
        }
        if self.intervals:
            ordered = sorted(self.intervals)
            data.update({
                "interval_mean_ms": round(statistics.fmean(ordered), 3),
                "interval_p50_ms": round(_percentile(ordered, 50), 3),
                "interval_p95_ms": round(_percentile(ordered, 95), 3),
                "interval_p99_ms": round(_percentile(ordered, 99), 3),
                "interval_max_ms": round(ordered[-1], 3),
            })
        return data


def _percentile(ordered_values: list[float], pct: float) -> float:
    if not ordered_values:
        return 0.0
    if len(ordered_values) == 1:
        return ordered_values[0]
    rank = (pct / 100.0) * (len(ordered_values) - 1)
    low = int(rank)
    high = min(low + 1, len(ordered_values) - 1)
    frac = rank - low
    return ordered_values[low] * (1.0 - frac) + ordered_values[high] * frac


def parse_artdmx(payload: bytes) -> tuple[int, int, int] | None:
    """Return (port_address, sequence, data_length) for ArtDmx packets, else None."""
    if len(payload) < 18 or payload[:8] != ARTNET_ID:
        return None
    opcode = struct.unpack_from("<H", payload, 8)[0]
    if opcode != OP_DMX:
        return None
    sequence = payload[12]
    subuni = payload[14]
    net = payload[15] & 0x7F
    length = struct.unpack_from(">H", payload, 16)[0]
    if len(payload) < 18 + length:
        return None
    return ((net << 8) | subuni, sequence, length)


class ArtNetProbe:
    def __init__(self, bind_addr: str = "0.0.0.0", port: int = ARTNET_PORT) -> None:
        self.bind_addr = bind_addr
        self.port = port
        self.universes: dict[int, UniverseStats] = {}
        self.non_dmx_packets = 0
        self._stop = threading.Event()
        self._sock: socket.socket | None = None

    def start(self) -> None:
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 1 << 21)
        self._sock.bind((self.bind_addr, self.port))
        self._sock.settimeout(0.25)

    def run(self, seconds: float) -> None:
        assert self._sock is not None, "call start() first"
        deadline = time.monotonic() + seconds
        while not self._stop.is_set() and time.monotonic() < deadline:
            try:
                payload, _ = self._sock.recvfrom(2048)
            except socket.timeout:
                continue
            now = time.monotonic()
            parsed = parse_artdmx(payload)
            if parsed is None:
                self.non_dmx_packets += 1
                continue
            port_address, sequence, length = parsed
            stats = self.universes.get(port_address)
            if stats is None:
                stats = UniverseStats(port_address=port_address)
                self.universes[port_address] = stats
            stats.observe(sequence, length, now)

    def stop(self) -> None:
        self._stop.set()

    def close(self) -> None:
        if self._sock is not None:
            self._sock.close()
            self._sock = None

    def report(self) -> dict:
        return {
            "universes": [s.summary() for s in
                          sorted(self.universes.values(), key=lambda u: u.port_address)],
            "non_artdmx_packets": self.non_dmx_packets,
        }


def print_report(report: dict, nominal_hz: float) -> int:
    nominal_ms = 1000.0 / nominal_hz
    rows = report["universes"]
    if not rows:
        print("No ArtDmx traffic captured. Check the VLAN, the firewall on UDP 6454, "
              "and the sender target address.")
        return 2

    header = (f"{'UNI':>6} {'PKTS':>7} {'Hz':>7} {'DROP':>6} {'DUP':>5} {'OOO':>5} "
              f"{'p50':>8} {'p95':>8} {'p99':>8} {'max':>8}")
    print(header)
    print("-" * len(header))
    worst = 0.0
    total_dropped = 0
    for row in rows:
        print(f"{row['universe']:>6} {row['packets']:>7} {row['hz']:>7.2f} "
              f"{row['dropped']:>6} {row['duplicates']:>5} {row['out_of_order']:>5} "
              f"{row.get('interval_p50_ms', 0):>8.2f} {row.get('interval_p95_ms', 0):>8.2f} "
              f"{row.get('interval_p99_ms', 0):>8.2f} {row.get('interval_max_ms', 0):>8.2f}")
        worst = max(worst, row.get("interval_p99_ms", 0.0))
        total_dropped += row["dropped"]

    print()
    print(f"Nominal period at {nominal_hz:g} Hz: {nominal_ms:.2f} ms; "
          f"worst p99 observed: {worst:.2f} ms")
    if report["non_artdmx_packets"]:
        print(f"Non-ArtDmx Art-Net packets (poll/sync/reply): {report['non_artdmx_packets']}")

    if total_dropped or worst > nominal_ms * 1.5:
        print("VERDICT: FAIL - network is not show-ready (loss or jitter above one DMX frame).")
        return 1
    print("VERDICT: PASS - jitter and loss within show tolerance.")
    return 0


def selftest() -> int:
    """Loopback test: synthesise a 44 Hz stream with an injected drop and verify detection."""
    probe = ArtNetProbe(bind_addr="127.0.0.1")
    probe.start()

    def sender() -> None:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        seq = 1
        for i in range(88):
            if i == 40:  # inject a two-frame loss
                seq = (seq + 2) % 256 or 1
            header = (ARTNET_ID + struct.pack("<H", OP_DMX) +
                      bytes([0, 14, seq, 0, 3, 0]) + struct.pack(">H", 512))
            sock.sendto(header + bytes(512), ("127.0.0.1", ARTNET_PORT))
            seq = 1 if seq == 255 else seq + 1
            time.sleep(1 / 44)
        sock.close()

    thread = threading.Thread(target=sender, daemon=True)
    thread.start()
    probe.run(seconds=2.5)
    thread.join(timeout=1.0)
    report = probe.report()
    probe.close()

    assert report["universes"], "no universes captured in selftest"
    uni = report["universes"][0]
    assert uni["universe"] == 3, f"unexpected port address {uni['universe']}"
    assert uni["dropped"] == 2, f"expected 2 dropped frames, got {uni['dropped']}"
    print(json.dumps(report, indent=2))
    print("SELFTEST OK")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Art-Net show network QA probe")
    parser.add_argument("--bind", default="0.0.0.0",
                        help="local interface to bind (use the lighting NIC address)")
    parser.add_argument("--port", type=int, default=ARTNET_PORT)
    parser.add_argument("--seconds", type=float, default=30.0, help="capture duration")
    parser.add_argument("--nominal-hz", type=float, default=44.0,
                        help="expected refresh rate per universe")
    parser.add_argument("--json", metavar="PATH", help="write the raw report to a JSON file")
    parser.add_argument("--selftest", action="store_true",
                        help="run a loopback self-test and exit")
    args = parser.parse_args()

    if args.selftest:
        return selftest()

    probe = ArtNetProbe(args.bind, args.port)
    probe.start()
    print(f"Capturing Art-Net on {args.bind}:{args.port} for {args.seconds:g} s ...")
    try:
        probe.run(args.seconds)
    except KeyboardInterrupt:
        probe.stop()
    report = probe.report()
    probe.close()

    if args.json:
        with open(args.json, "w", encoding="utf-8") as handle:
            json.dump(report, handle, indent=2)
        print(f"Report written to {args.json}")

    return print_report(report, args.nominal_hz)


if __name__ == "__main__":
    sys.exit(main())
