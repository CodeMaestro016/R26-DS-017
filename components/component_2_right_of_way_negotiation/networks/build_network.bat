@echo off
setlocal

if defined SUMO_HOME (
    set "NETCONVERT=%SUMO_HOME%\bin\netconvert.exe"
) else (
    set "NETCONVERT=netconvert"
)

pushd "%~dp0"
"%NETCONVERT%" ^
  --node-files intersection.nod.xml ^
  --edge-files intersection.edg.xml ^
  --connection-files intersection.con.xml ^
  --output-file intersection.net.xml ^
  --no-turnarounds true

if errorlevel 1 (
    echo.
    echo Network generation failed.
    echo Set SUMO_HOME or add the SUMO bin directory to PATH.
    popd
    exit /b 1
)

echo Generated intersection.net.xml successfully.
popd
endlocal

