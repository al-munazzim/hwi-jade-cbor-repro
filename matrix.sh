#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DRY_RUN="${1:-}"
CBOR_VERSIONS=(5.7.1 5.8.0 5.9.0)
MODES=(stock patched)

if [[ "$DRY_RUN" == "--dry-run" ]]; then
  echo "Plan:"
  for v in "${CBOR_VERSIONS[@]}"; do
    for m in "${MODES[@]}"; do
      echo "- cbor2==$v mode=$m"
      echo "  create .venv-matrix-${v//./_}-${m}, install hwi==3.2.0 cbor2==$v"
      echo "  run: python repro.py --$m"
    done
  done
  exit 0
fi

declare -A RESULT

for v in "${CBOR_VERSIONS[@]}"; do
  for m in "${MODES[@]}"; do
    venv="$ROOT/.venv-matrix-${v//./_}-${m}"
    rm -rf "$venv"
    python3 -m venv "$venv"
    "$venv/bin/pip" install --upgrade pip >/dev/null
    "$venv/bin/pip" install "hwi==3.2.0" "cbor2==$v" >/dev/null

    set +e
    output="$($venv/bin/python "$ROOT/repro.py" --$m 2>&1)"
    code=$?
    set -e

    cell="ERROR"
    if grep -q "FROZEN" <<<"$output"; then
      cell="FROZEN"
    elif [[ $code -eq 0 ]]; then
      cell="PASS"
    fi

    RESULT["$m,$v"]="$cell"
    printf "[%s cbor2=%s] %s\n" "$m" "$v" "$cell"
  done
done

echo
echo "| mode \\ cbor2 | 5.7.1 | 5.8.0 | 5.9.0 |"
echo "|---|---|---|---|"
for m in "${MODES[@]}"; do
  echo "| $m | ${RESULT[$m,5.7.1]} | ${RESULT[$m,5.8.0]} | ${RESULT[$m,5.9.0]} |"
done
