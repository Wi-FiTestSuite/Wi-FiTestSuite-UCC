@echo off
REM #################################################################
REM This batch file runs the UCC script for given for AP_CAPI_Test
REM Usage - 11n_AP_Agent_Test
REM #################################################################


REM Path for the UCC command files folder
set UCC_CMD_PATH=..\..\cmds\Sigma-11n
C:\python25\python wfa_ucc.py 1 init_AP_compliance.txt AP_CAPI_compliance_Test_TCL.txt