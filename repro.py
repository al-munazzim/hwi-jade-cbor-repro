#!/usr/bin/env python3
"""Reproduce Jade + cbor2 stream-read behavior through HWI."""

from __future__ import annotations

import argparse
import signal
import sys
from contextlib import contextmanager

from hwilib import commands
from hwilib.errors import DeviceNotReadyError

CANNED_PSBT = (
    "cHNidP8BAHUCAAAAASaBcTce3/KF6Tet7qSze3gADAVmy7OtZGQXE8pCFxv2AAAAAAD+////"
    "AtPf9QUAAAAAGXapFNDFmQPFusKGh2DpD9UhpGZap2UgiKwA4fUFAAAAABepFDVF5uM7gyxHBQ"
    "8k0+65PJwDlIvHh7MuEwAAAQD9pQEBAAAAAAECiaPHHqtNIOA3G7ukzGmPopXJRjr6Ljl/hTPM"
    "ti+VZ+UBAAAAFxYAFL4Y0VKpsBIDna89p95PUzSe7LmF/////4b4qkOnHf8USIk6UwpyN+9rRgi"
    "7st0tAXHmOuxqSJC0AQAAABcWABT+Pp7xp0XpdNkCxDVZQ6vLNL1TU/////8CAMLrCwAAAAAZdq"
    "kUhc/xCX/Z4Ai7NK9wnGIZeziXikiIrHL++E4sAAAAF6kUM5cluiHv1irHU6m80GfWx6ajnQWHA"
    "kcwRAIgJxK+IuAnDzlPVoMR3HyppolwuAJf3TskAinwf4pfOiQCIAGLONfc0xTnNMkna9b7QPZz"
    "MlvEuqFEyADS8vAtsnZcASED0uFWdJQbrUqZY3LLh+GFbTZSYG2YVi/jnF6efkE/IQUCSDBFAiE"
    "A0SuFLYXc2WHS9fSrZgZU327tzHlMDDPOXMMJ/7X85Y0CIGczio4OFyXBl/saiK9Z9R5E5CVbIB"
    "Z8hoQDHAXR8lkqASECI7cr7vCWXRC+B3jv7NYfysb3mk6haTkzgHNEZPhPKrMAAAAAAA=="
)


class StepTimeout(RuntimeError):
    pass


@contextmanager
def timeout(seconds: int, step: str):
    def _handler(_sig, _frame):
        raise StepTimeout(f"FROZEN {step}")

    prev = signal.signal(signal.SIGALRM, _handler)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, prev)


def run_step(name: str, fn):
    try:
        with timeout(30, name):
            return fn()
    except StepTimeout as exc:
        print(str(exc))
        sys.exit(2)


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--patched", action="store_true", help="Apply candidate monkey-patch")
    mode.add_argument("--stock", action="store_true", help="Skip monkey-patch")
    parser.add_argument("--skip-sign", action="store_true", help="Only enumerate + xpub steps")
    args = parser.parse_args()

    if args.patched:
        import patch

        patch.apply()

    devices = run_step("enumerate", lambda: commands.enumerate(allow_emulators=False))
    jade = next((d for d in devices if d.get("type") == "jade"), None)
    if not jade:
        print("NO JADE; exiting")
        return 10

    try:
        client = commands.get_client(jade["type"], jade["path"])
    except DeviceNotReadyError as exc:
        print(f"JADE LOCKED; exiting ({exc})")
        return 11
    if client is None:
        print("ERROR could not open Jade client")
        return 1

    try:
        xpub = run_step("getxpub", lambda: commands.getxpub(client, "m/84h/1h/0h"))
        print(f"OK getxpub {xpub.get('xpub', '')[:24]}...")

        if not args.skip_sign:
            result = run_step("signtx", lambda: commands.signtx(client, CANNED_PSBT))
            print(f"OK signtx keys={list(result.keys())}")
    finally:
        try:
            client.close()
        except Exception:
            pass

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
