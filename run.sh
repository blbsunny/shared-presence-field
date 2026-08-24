#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"
echo "============================================================"
echo " Shared Presence Field  --  sample pipeline"
echo " The first run sets up a local Python environment and can"
echo " take a few minutes. Please wait; do not close this window."
echo "============================================================"
echo
if [ ! -d .venv ]; then
    echo "[1/3] Creating a local virtual environment (.venv) ..."
    python3 -m venv .venv
else
    echo "[1/3] Reusing existing .venv ..."
fi
source .venv/bin/activate
echo "[2/3] Installing numpy / scipy / matplotlib (first time only, please wait) ..."
python -m pip install -r requirements.txt
echo "[3/3] Running the analysis ..."
echo
python -u run_all.py
echo
if [ "$(uname)" = "Darwin" ]; then open out; else xdg-open out; fi
