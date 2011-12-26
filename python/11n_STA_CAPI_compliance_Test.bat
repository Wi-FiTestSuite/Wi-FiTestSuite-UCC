@echo off
REM #################################################################
REM This batch file runs the UCC script for given for AP_CAPI_Test
REM Usage - 11n_AP_Agent_Test
REM #################################################################


REM Path for the UCC command files folder
set UCC_CMD_PATH=..\..\cmds\Sigma-11n
C:\python25\python wfa_ucc.py 1 init_STA_compliance.txt STA_CAPI_compliance_Test.txt
