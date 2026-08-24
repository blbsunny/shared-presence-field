@echo off
cd /d "%~dp0"
echo ============================================================
echo  Shared Presence Field  --  sample pipeline
echo  The first run sets up a local Python environment and can
echo  take a few minutes. Please wait; do not close this window.
echo ============================================================
echo.
if not exist .venv (
    echo [1/3] Creating a local virtual environment (.venv) ...
    python -m venv .venv
) else (
    echo [1/3] Reusing existing .venv ...
)
call .venv\Scripts\activate
echo [2/3] Installing numpy / scipy / matplotlib (first time only, please wait) ...
python -m pip install -r requirements.txt
echo [3/3] Running the analysis ...
echo.
python -u run_all.py
echo.
start "" "out"
pause
