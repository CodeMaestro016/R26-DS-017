@REM Disable command echo while running the demo launcher.
@echo off
REM Localize environment changes made by this launcher.
setlocal

REM Generate the network only if the expected network XML file is absent.
if not exist "networks\intersection.net.xml" (
    REM Call the companion network builder and return here when it completes.
    call "networks\build_network.bat"
    REM Stop the launcher with an error code if network generation failed.
    if errorlevel 1 exit /b 1
)

REM Start the selected MAPPO demonstration with the SUMO graphical interface enabled.
python run_selected_mappo_demo.py --gui
REM End the launcher's localized environment scope.
endlocal
