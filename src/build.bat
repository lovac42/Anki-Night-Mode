@echo off
set ZIP=C:\PROGRA~1\7-Zip\7z.exe a -tzip -y -r
set REPO=night_mode
set NAME=Night Mode for CCBC
set PACKID=night_mode
set VERSION=3.0.0


quick_manifest.exe "%NAME%" "%PACKID%" >%REPO%\manifest.json
echo %VERSION% >%REPO%\VERSION

fsum -r -jm -md5 -d%REPO% * > checksum.md5
move checksum.md5 %REPO%\checksum.md5

REM %ZIP% %REPO%_v%VERSION%_Anki20.zip *.py %REPO%\*
cd %REPO%
REM %ZIP% ../%REPO%_v%VERSION%_Anki21.ankiaddon *
%ZIP% ../%REPO%_v%VERSION%_CCBC.adze *
