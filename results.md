# HWI Jade + cbor2 Matrix Results

Paste output from `./matrix.sh` below.

## Environment
- OS: macOS 15.4.1 (24E263)
- Python: 3.9.23
- Jade signer: temporary SeedQR signer
- HWI: 3.2.0

## Matrix

| mode \ cbor2 | 5.7.1 | 5.8.0 | 5.9.0 |
|---|---|---|---|
| stock | PASS | FROZEN | PASS |
| patched | PASS | PASS | PASS |

Legend: PASS = completed `signtx`; FROZEN = timeout; SKIP = no Jade or Jade locked.

## Raw output

```text
[stock cbor2=5.7.1] PASS (log: /Users/kim/src/hwi-jade-cbor-repro/matrix-logs/stock-cbor2-5.7.1.log)
[patched cbor2=5.7.1] PASS (log: /Users/kim/src/hwi-jade-cbor-repro/matrix-logs/patched-cbor2-5.7.1.log)
[stock cbor2=5.8.0] FROZEN (log: /Users/kim/src/hwi-jade-cbor-repro/matrix-logs/stock-cbor2-5.8.0.log)
[patched cbor2=5.8.0] PASS (log: /Users/kim/src/hwi-jade-cbor-repro/matrix-logs/patched-cbor2-5.8.0.log)
[stock cbor2=5.9.0] PASS (log: /Users/kim/src/hwi-jade-cbor-repro/matrix-logs/stock-cbor2-5.9.0.log)
[patched cbor2=5.9.0] PASS (log: /Users/kim/src/hwi-jade-cbor-repro/matrix-logs/patched-cbor2-5.9.0.log)

| mode \ cbor2 | 5.7.1 | 5.8.0 | 5.9.0 |
|---|---|---|---|
| stock | PASS | FROZEN | PASS |
| patched | PASS | PASS | PASS |

Logs saved under: /Users/kim/src/hwi-jade-cbor-repro/matrix-logs
Legend: PASS=completed signtx, FROZEN=timeout, SKIP/NO_JADE=no Jade, SKIP/JADE_LOCKED=Jade locked
```

## Notes for upstream PR
- HWI issue: https://github.com/bitcoin-core/HWI/issues/817
- Security advisory motivating >=5.9.0: https://github.com/advisories/GHSA-3c37-wwvx-h642
- Candidate patch: `patch.py` (monkey-patch implementation intended to map to `JadeInterface.read` in HWI)
