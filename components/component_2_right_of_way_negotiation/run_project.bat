@echo off
setlocal

if not exist "networks\intersection.net.xml" (
    call "networks\build_network.bat"
    if errorlevel 1 exit /b 1
)

python run_selected_mappo_demo.py --gui
endlocal
