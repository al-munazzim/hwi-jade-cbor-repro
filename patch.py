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

    cbor2>=5.8 may request a large buffered read (e.g. 4096). Passing that
    straight to pyserial blocks for full-length reads and stalls Jade.

    Important: small reads are framing-critical for cbor decoding and should
    remain exact-length requests. Only clamp obviously buffered large reads.
    """
    from hwilib.devices.jadepy.jade import JadeInterface

    def _patched_read(self, n):
        import logging

        logger = logging.getLogger(__name__)
        logger.debug("Reading %s bytes...", n)

        want = max(1, int(n))

        # Preserve exact semantics for normal protocol-sized reads.
        if want >= 4096:
            available = _available_now(self.impl)
            if isinstance(available, int) and available > 0:
                want = min(want, available)
            else:
                want = 1

        data = self.impl.read(want)
        logger.debug("Received: %s bytes", len(data))
        return data

    JadeInterface.read = _patched_read
