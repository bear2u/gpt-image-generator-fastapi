#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${ROOT_DIR}/.venv"
HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-8310}"

find_python() {
  for candidate in "${PYTHON:-}" python3.12 python3.11 python3.10 python3; do
    if [[ -n "${candidate}" ]] && command -v "${candidate}" >/dev/null 2>&1; then
      if "${candidate}" - <<'PY' >/dev/null 2>&1
import sys
raise SystemExit(0 if sys.version_info >= (3, 10) else 1)
PY
      then
        command -v "${candidate}"
        return 0
      fi
    fi
  done

  echo "Python 3.10+ is required. Set PYTHON=/path/to/python3.12 or install Python 3.10+." >&2
  return 1
}

PYTHON_BIN="$(find_python)"

if [[ ! -x "${VENV_DIR}/bin/python" ]]; then
  echo "Creating virtualenv at ${VENV_DIR}"
  "${PYTHON_BIN}" -m venv "${VENV_DIR}"
fi

echo "Installing Python server dependencies"
"${VENV_DIR}/bin/python" -m pip install --upgrade pip
"${VENV_DIR}/bin/python" -m pip install -e "${ROOT_DIR}/python[server]"

echo "Starting Gpt-imagen v2 at http://${HOST}:${PORT}"
cd "${ROOT_DIR}"
exec "${VENV_DIR}/bin/uvicorn" gti.server:app --host "${HOST}" --port "${PORT}" --reload
