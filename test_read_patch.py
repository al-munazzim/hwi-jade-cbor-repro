"""Unit tests for JadeInterface.read behavior with large decoder reads."""

from __future__ import annotations

import time

import pytest
from hwilib.devices.jadepy.jade import JadeInterface

import patch


class FakeSerial:
    def __init__(self, data: bytes):
        self._buf = bytearray(data)

    @property
    def in_waiting(self) -> int:
        return len(self._buf)

    def read(self, n: int) -> bytes:
        if n <= 0:
            return b""
        if n > len(self._buf):
            time.sleep(0.15)  # emulate waiting for unavailable bytes
            return b""
        out = bytes(self._buf[:n])
        del self._buf[:n]
        return out


class FakeSerialImpl:
    def __init__(self, data: bytes):
        self.ser = FakeSerial(data)

    def read(self, n: int) -> bytes:
        return self.ser.read(n)


def _make_interface(payload: bytes) -> JadeInterface:
    return JadeInterface(FakeSerialImpl(payload))


def test_stock_read_times_out_with_large_request():
    iface = _make_interface(b"hello")
    start = time.monotonic()
    out = iface.read(4096)
    elapsed = time.monotonic() - start

    assert out == b""
    assert elapsed >= 0.14


def test_patched_read_returns_short_data_promptly_without_loss():
    patch.apply()
    payload = b"abcdefghijklmnopqrstuvwxyz"
    iface = _make_interface(payload)

    chunks = []
    while True:
        chunk = iface.read(4096)
        if not chunk:
            break
        chunks.append(chunk)

    assert b"".join(chunks) == payload
    assert all(1 <= len(c) <= 26 for c in chunks)


def test_patched_read_is_prompt_for_large_request():
    patch.apply()
    iface = _make_interface(b"xyz")

    start = time.monotonic()
    out = iface.read(4096)
    elapsed = time.monotonic() - start

    assert out == b"xyz"
    assert elapsed < 0.05


def test_patched_small_reads_keep_exact_length_behavior():
    patch.apply()
    iface = _make_interface(b"abcdef")

    start = time.monotonic()
    out = iface.read(11)
    elapsed = time.monotonic() - start

    assert out == b""
    assert elapsed >= 0.14


def test_patched_protocol_sized_reads_keep_exact_length_behavior():
    patch.apply()
    iface = _make_interface(b"x" * 27)

    start = time.monotonic()
    out = iface.read(336)
    elapsed = time.monotonic() - start

    assert out == b""
    assert elapsed >= 0.14
