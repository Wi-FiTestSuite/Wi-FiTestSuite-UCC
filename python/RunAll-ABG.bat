@echo off
cls
REM #################################################################
REM This batch file runs All the WMM UCC scripts 
REM Usage - RunAll
REM #################################################################


REM Path for the UCC command files folder
set UCC_CMD_PATH=..\cmds\Sigma-WMM\Sigma-WMM-ABG
set isValid=
IF NOT "%1"=="" GOTO HELP

echo .
echo          Running Version 1.6 - WMM System Interoperability Test Plan
echo .


FOR /F "eol=# tokens=1,2,3 delims=!" %%A in ('findstr "!" Sigma-WMM') do (
set isValid=1
echo .
echo #################################################################
echo          Running Testcase - %%A 
echo #################################################################
echo .
wfa_ucc.exe 1 %%B %%C
)

IF NOT "%isValid%"=="1" echo No Tests Run - %1

GOTO EOF

:HELP
echo "Usage - RunAll"

:EOF