# hwi-jade-cbor-repro

Minimal testbed for the HWI Jade regression triggered by `cbor2>=5.8.0`, plus a candidate patch suitable for upstream HWI.

## 1) The bug

In HWI 3.2.0, `hwilib/devices/jadepy/jade.py` has:

```python
def read(self, n):
    bytes_ = self.impl.read(n)
    return bytes_
```

`self.impl` usually wraps pyserial. `pyserial.Serial.read(n)` waits for up to `n` bytes (or timeout).  
With `cbor2>=5.8.0`, decoder stream reads became buffered and can request large chunks (`read(4096)`). Jade replies are much smaller, so `read(4096)` blocks until timeout and signing appears frozen.

Tracking issue: https://github.com/bitcoin-core/HWI/issues/817

## 2) Why the existing workaround fails

Issue #817 was closed with a workaround (pin `cbor2==5.7.1`). That is no longer acceptable because `cbor2` 5.7.1 is vulnerable to:
- GHSA-3c37-wwvx-h642 (high-severity DoS in `cbor2.loads`)
- First patched in `cbor2>=5.9.0`

So downstreams that need secure `cbor2` lose Jade unless HWI is fixed.

## 3) Run the matrix (Jade attached)

```bash
./matrix.sh
```

This runs `repro.py` across:
- cbor2: `5.7.1`, `5.8.0`, `5.9.0`
- modes: `stock`, `patched`

It creates fresh per-cell virtualenvs and tries to install `hwi==3.2.0` + `cbor2==<version>`.
If the wheel is unavailable for your Python (for example Python 3.13), it automatically falls back to installing HWI 3.2.0 from source in that venv, then runs the repro and prints a 2x3 PASS/FROZEN/ERROR markdown table.

Preview only:

```bash
./matrix.sh --dry-run
```

## 4) Where the patch lives

- Candidate patch module: `patch.py`
- Entry point: `patch.apply()`
- It monkey-patches `hwilib.devices.jadepy.jade.JadeInterface.read`

Behavior: for large read requests, it reads only bytes already buffered (if known), otherwise falls back to requesting 1 byte to avoid long blocking on transports with pyserial-like semantics.

## 5) How an HWI maintainer can adopt it upstream

1. Open `hwilib/devices/jadepy/jade.py` in HWI.
2. Replace `JadeInterface.read()` logic with the function in `patch.py` (same signature).
3. Add tests equivalent to `test_read_patch.py`.
4. Validate against a real Jade using the matrix in this repo.

This keeps behavior transport-agnostic and addresses the cbor2 buffered-read change without pinning a vulnerable version.
