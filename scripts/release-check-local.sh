#!/usr/bin/env bash
set -eu

ROOT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
WORK_DIR="$(mktemp -d)"
cleanup() {
  rm -rf "$WORK_DIR"
}
trap cleanup EXIT

DIST_DIR="$WORK_DIR/dist"
VENV_DIR="$WORK_DIR/venv"
mkdir -p "$DIST_DIR"

cd "$ROOT_DIR"

if ! python -c "import wheel" >/dev/null 2>&1; then
  cat >&2 <<'EOF'
Local release check requires the Python 'wheel' package in the current environment.
Install it or run this check in a build environment that can satisfy pyproject.toml build requirements.
EOF
  exit 2
fi

python -m pip wheel --no-build-isolation --no-deps . --wheel-dir "$DIST_DIR" >/dev/null
python setup.py sdist --dist-dir "$DIST_DIR" >/dev/null

python -m venv --system-site-packages "$VENV_DIR"
"$VENV_DIR/bin/python" -m pip install --no-deps "$DIST_DIR"/*.whl >/dev/null

"$VENV_DIR/bin/dpawb" capabilities >/dev/null
"$VENV_DIR/bin/dpawb" assess \
  --profile "$ROOT_DIR/fixtures/profiles/synthetic_evolution_latest.yaml" >/dev/null
"$VENV_DIR/bin/dpawb" coverage \
  --profile "$ROOT_DIR/fixtures/profiles/synthetic_evolution_latest.yaml" \
  --use-case "$ROOT_DIR/fixtures/use_cases/product_identity_lookup.yaml" >/dev/null

python - "$DIST_DIR" <<'PY'
from pathlib import Path
import sys

dist = Path(sys.argv[1])
artifacts = sorted(path.name for path in dist.iterdir())
if not any(name.endswith(".whl") for name in artifacts):
    raise SystemExit("wheel artifact was not produced")
if not any(name.endswith(".tar.gz") for name in artifacts):
    raise SystemExit("sdist artifact was not produced")
print("\n".join(artifacts))
PY
