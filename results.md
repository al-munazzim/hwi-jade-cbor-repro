# HWI Jade + cbor2 Matrix Results

Paste output from `./matrix.sh` below.

## Environment
- OS:
- Python:
- Jade firmware:
- HWI: 3.2.0

## Matrix

| mode \ cbor2 | 5.7.1 | 5.8.0 | 5.9.0 |
|---|---|---|---|
| stock |  |  |  |
| patched |  |  |  |

Legend: PASS = completed `signtx`; FROZEN = timeout; SKIP = no Jade or Jade locked.

## Raw output

```text
(paste ./matrix.sh output here)
```

## Notes for upstream PR
- HWI issue: https://github.com/bitcoin-core/HWI/issues/817
- Security advisory motivating >=5.9.0: https://github.com/advisories/GHSA-3c37-wwvx-h642
- Candidate patch: `patch.py` (monkey-patch implementation intended to map to `JadeInterface.read` in HWI)
