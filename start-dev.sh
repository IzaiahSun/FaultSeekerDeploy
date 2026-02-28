#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────
# start-dev.sh  —  Launch FaultSeeker in development mode
#                  (no Docker required)
# ─────────────────────────────────────────────────────────
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# ── Check .env ───────────────────────────────────────────
if [ ! -f .env ]; then
  echo "[ERROR] .env file not found."
  echo "  Copy .env.example to .env and fill in your API key."
  exit 1
fi

# ── Check Foundry (cast) ──────────────────────────────────
if ! command -v cast &>/dev/null; then
  echo "[ERROR] 'cast' (Foundry) is not installed or not in PATH."
  echo "  Install with: curl -L https://foundry.paradigm.xyz | bash && foundryup"
  exit 1
fi

# ── Python virtual environment ───────────────────────────
if [ ! -d venv ]; then
  echo "[INFO] Creating Python virtual environment..."
  python3 -m venv venv
fi

echo "[INFO] Installing Python dependencies..."
venv/bin/pip install --quiet -r requirements.txt
venv/bin/pip install --quiet -r backend/requirements.txt
venv/bin/pip install --quiet -e .

# ── Node dependencies ─────────────────────────────────────
echo "[INFO] Installing Node dependencies..."
cd frontend && npm install --silent && cd ..

# ── Start backend ─────────────────────────────────────────
echo "[INFO] Starting backend on http://localhost:8000 ..."
venv/bin/uvicorn backend.main:app --reload --port 8000 &
BACKEND_PID=$!

# ── Start frontend ────────────────────────────────────────
echo "[INFO] Starting frontend on http://localhost:5173 ..."
cd frontend && npm run dev &
FRONTEND_PID=$!

echo ""
echo "  Backend  → http://localhost:8000"
echo "  Frontend → http://localhost:5173"
echo ""
echo "  Press Ctrl+C to stop both servers."

# ── Cleanup on exit ───────────────────────────────────────
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; echo 'Stopped.'" EXIT INT TERM
wait
