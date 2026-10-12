@echo off
setlocal DisableDelayedExpansion
set "PYTHONIOENCODING=utf-8"
rem Run from the project directory, including paths containing spaces or Unicode.
pushd "%~dp0"
if errorlevel 1 exit /b 1

rem Prefer PATH's interpreter (also honours CI/venvs), then the Python launcher.
python -X utf8 -c "import sys; sys.exit(sys.version_info < (3, 9))" >nul 2>&1
if not errorlevel 1 (
    set "PIM_WINDOWS_PYTHON=python"
    goto ready
)
py -3 -X utf8 -c "import sys; sys.exit(sys.version_info < (3, 9))" >nul 2>&1
if not errorlevel 1 (
    set "PIM_WINDOWS_PYTHON=py -3"
    goto ready
)
echo Python 3.9 or later is required. Install Python with its launcher or add it to PATH.
set "PIM_WINDOWS_EXIT=1"
goto cleanup

:ready
if "%~1"=="--check" goto check
if not "%~1"=="" goto usage
%PIM_WINDOWS_PYTHON% -X utf8 main.py
goto finish

:check
%PIM_WINDOWS_PYTHON% -X utf8 tools\check_coverage.py
if errorlevel 1 goto finish
%PIM_WINDOWS_PYTHON% -X utf8 -m compileall -q model controller cli storage view tests tools main.py
goto finish

:usage
echo Usage: run_windows.cmd [--check]
set "PIM_WINDOWS_EXIT=2"
goto cleanup

:finish
set "PIM_WINDOWS_EXIT=%errorlevel%"
:cleanup
popd
exit /b %PIM_WINDOWS_EXIT%
