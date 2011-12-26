@echo off
cls


REM Path for the UCC command files folder
set UCC_CMD_PATH=..\cmds\Sigma-WMM-Prototype\Sigma-WMM-BB-Prototype
set isValid=
IF "%1"=="" GOTO HELP

wfa_ucc.exe 1 init_WMM.txt WMM-S1-T02.txt
wfa_ucc.exe 1 init_WMM.txt WMM-S1-T03.txt

REM Downstream calibration
wfa_ucc.exe 1 init_WMM.txt WMM-S1-T04.txt

REM Upstream calibration
wfa_ucc.exe 1 init_WMM.txt WMM-S1-T05.txt
