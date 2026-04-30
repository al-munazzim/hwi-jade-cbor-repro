#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DRY_RUN="${1:-}"
CBOR_VERSIONS=(5.7.1 5.8.0 5.9.0)
MODES=(stock patched)
LOG_DIR="$ROOT/matrix-logs"

if [[ "$DRY_RUN" == "--dry-run" ]]; then
  echo "Plan:"
  for v in "${CBOR_VERSIONS[@]}"; do
    for m in "${MODES[@]}"; do
      echo "- cbor2==$v mode=$m"
      echo "  create .venv-matrix-${v//./_}-${m}, install hwi==3.2.0 cbor2==$v"
      echo "  run: python repro.py --$m"
      echo "  log: matrix-logs/${m}-cbor2-${v}.log"
    done
  done
  exit 0
fi

declare -A RESULT
rm -rf "$LOG_DIR"
mkdir -p "$LOG_DIR"

install_hwi() {
  local venv="$1"
  local cbor_ver="$2"

  if "$venv/bin/pip" install "hwi==3.2.0" "cbor2==$cbor_ver" >/dev/null 2>&1; then
    return 0
  fi

  echo "hwi==3.2.0 wheel unavailable for this Python; falling back to source install" >&2
  local src="$ROOT/.hwi-src"
  rm -rf "$src"
  git -c advice.detachedHead=false clone --depth 1 --branch 3.2.0 https://github.com/bitcoin-core/HWI.git "$src" >/dev/null

  PIP_IGNORE_REQUIRES_PYTHON=1 "$venv/bin/pip" install --no-deps "$src" >/dev/null
  "$venv/bin/pip" install \
    "cbor2==$cbor_ver" \
    ecdsa hidapi libusb1 mnemonic noiseprotocol "protobuf<5" pyaes semver typing-extensions pyserial >/dev/null
}

for v in "${CBOR_VERSIONS[@]}"; do
  for m in "${MODES[@]}"; do
    venv="$ROOT/.venv-matrix-${v//./_}-${m}"
    log="$LOG_DIR/${m}-cbor2-${v}.log"
    rm -rf "$venv"
    python3 -m venv "$venv"
    "$venv/bin/pip" install --upgrade pip >/dev/null

    set +e
    {
      install_hwi "$venv" "$v"
      "$venv/bin/python" "$ROOT/repro.py" --$m
    } >"$log" 2>&1
    code=$?
    set -e

    output="$(cat "$log")"
    cell="ERROR"
    if grep -q "FROZEN" <<<"$output"; then
      cell="FROZEN"
    elif [[ $code -eq 0 ]]; then
      cell="PASS"
    fi

    RESULT["$m,$v"]="$cell"
    printf "[%s cbor2=%s] %s (log: %s)\n" "$m" "$v" "$cell" "$log"
    if [[ "$cell" == "ERROR" ]]; then
      echo "--- ERROR tail ($m, $v) ---"
      tail -n 40 "$log"
      echo "--- end tail ---"
    fi
  done
done

rm -rf "$ROOT/.hwi-src"

echo
echo "| mode \\ cbor2 | 5.7.1 | 5.8.0 | 5.9.0 |"
echo "|---|---|---|---|"
for m in "${MODES[@]}"; do
  echo "| $m | ${RESULT[$m,5.7.1]} | ${RESULT[$m,5.8.0]} | ${RESULT[$m,5.9.0]} |"
done

echo
echo "Logs saved under: $LOG_DIR"
