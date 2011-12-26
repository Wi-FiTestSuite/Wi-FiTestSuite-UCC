@echo off
cls
REM #################################################################
REM This batch file runs the UCC script for given WMM testcases Name
REM Usage - wmmTest <WMM Testcase Name>
REM #################################################################


REM Path for the UCC command files folder
set UCC_CMD_PATH=..\cmds\Sigma-WMM\Sigma-WMM-BG
set isValid=
IF "%1"=="" GOTO HELP

echo .
echo          Running Testcase - %1 * [Version 1.6 - WMM System Interoperability Test Plan]
echo .


FOR /F "eol=# tokens=2,3 delims=!" %%A in ('findstr /C:"%1!" Sigma-WMM') do (
set isValid=1
wfa_ucc.exe 1 %%A %%B
)

IF NOT "%isValid%"=="1" echo Invalid Testcase Name - %1

GOTO EOF

:HELP
echo "Usage - wmmTest <WMM Testcase Name>"
echo "Testcase Name should be one of the following - "
echo WMM-S2-T04

:EOF