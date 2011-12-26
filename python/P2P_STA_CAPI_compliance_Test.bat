@echo off
REM #################################################################
REM This batch file runs the UCC script for given for AP_CAPI_Test
REM Usage - 11n_AP_Agent_Test
REM #################################################################


REM Path for the UCC command files folder
set UCC_CMD_PATH=..\..\cmds\Sigma-P2P
REM C:\python25\python wfa_ucc.py 1 init_STA_compliance.txt P2P-CAPI-Test.txt

C:\python25\python wfa_ucc.py 1 init_STA_compliance.txt Test3-Group_Formation.txt