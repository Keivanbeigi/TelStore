@echo off
REM Crypto Quest bot - launcher for Windows Task Scheduler
REM Runs the bot as an independent process (not tied to Hermes sessions).
REM Logs to bot.log in the same directory.
REM PYTHONIOENCODING forces UTF-8 so emoji in log output don't crash on cp1252.

set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1

cd /d "E:\My Documents\Crypto Quest\github\scripts"

REM Use the python on PATH; the bot needs only the standard library.
python -u bot.py >> "E:\My Documents\Crypto Quest\github\scripts\bot.log" 2>&1