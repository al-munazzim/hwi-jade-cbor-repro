"""Runtime monkey-patch for HWI JadeInterface.read()."""

from __future__ import annotations


def _available_now(impl) -> int | None:
    """Best-effort query of already-buffered bytes on the transport."""
    ser = getattr(impl, "ser", None)
    if ser is not None:
        waiting = getattr(ser, "in_waiting", None)
        if isinstance(waiting, int):
            return waiting

    waiting = getattr(impl, "in_waiting", None)
    if callable(waiting):
        waiting = waiting()
    if isinstance(waiting, int):
        return waiting

    return None


def apply() -> None:
    """Patch HWI's JadeInterface.read to avoid large blocking reads.

    cbor2>=5.8 may call read(4096). Passing that directly into pyserial blocks
    until all bytes (or timeout), which stalls Jade even though only a short
    frame is ready. We ask for currently buffered bytes (or 1 byte fallback),
    return promptly, and let the decoder pull again as needed.
    """
    from hwilib.devices.jadepy.jade import JadeInterface

    def _patched_read(self, n):
        import logging

        logger = logging.getLogger(__name__)
        logger.debug("Reading %s bytes...", n)

        want = max(1, int(n))
        available = _available_now(self.impl)
        if isinstance(available, int) and available > 0:
            want = min(want, available)
        elif want > 1:
            want = 1

        data = self.impl.read(want)
        logger.debug("Received: %s bytes", len(data))
        return data

    JadeInterface.read = _patched_read
