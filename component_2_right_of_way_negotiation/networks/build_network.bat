@REM Disable command echo so the launcher reports its own messages rather than every command.
@echo off
REM Localize environment changes to this batch invocation.
setlocal

REM Choose the SUMO-installed converter when its installation directory is configured.
if defined SUMO_HOME (
    REM Resolve the network converter inside the configured SUMO installation.
    set "NETCONVERT=%SUMO_HOME%\bin\netconvert.exe"
REM Use the fallback command when no SUMO installation directory is configured.
) else (
    REM Resolve netconvert through the caller's PATH.
    set "NETCONVERT=netconvert"
)

REM Save the caller's directory and work beside the network input files.
pushd "%~dp0"
REM Build the network from the node, edge, and connection XML files listed below.
REM Write intersection.net.xml and disable automatically generated turnarounds.
REM The following command uses caret continuation, so its option lines stay adjacent.
"%NETCONVERT%" ^
  --node-files intersection.nod.xml ^
  --edge-files intersection.edg.xml ^
  --connection-files intersection.con.xml ^
  --output-file intersection.net.xml ^
  --no-turnarounds true

REM Check the converter exit status before reporting success.
if errorlevel 1 (
    REM Print a blank line before the failure explanation.
    echo.
    REM Report that network generation failed.
    echo Network generation failed.
    REM Explain how the user can make the SUMO converter available.
    echo Set SUMO_HOME or add the SUMO bin directory to PATH.
    REM Restore the caller's directory before returning from this failure path.
    popd
    REM Return a nonzero exit code to the calling script.
    exit /b 1
)

REM Report the successful output filename.
echo Generated intersection.net.xml successfully.
REM Restore the caller's original working directory.
popd
REM End the localized environment scope.
endlocal

