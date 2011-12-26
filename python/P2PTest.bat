@echo off
cls
REM #################################################################
REM This batch file runs the UCC script for given P2P testcases Name
REM Usage - P2PTest <P2P Testcase Name>
REM #################################################################


REM Path for the UCC command files folder
set UCC_CMD_PATH=..\cmds\Sigma-P2P
set PROG_NAME=P2P
set isValid=
echo .
echo          Running Testcase - %1 * 
echo .

del result.html

IF "%1"=="" GOTO HELP
IF "%1"=="group" GOTO GROUP

IF "%1"=="all" GOTO ALL
IF NOT "%1"=="all" GOTO SINGLE

:ALL
set searchString=P2P
GOTO S
:SINGLE
set searchString=%1
GOTO S

:S
	FOR /F "eol=# tokens=2,3 delims=!" %%A in ('findstr "%searchString%!" Sigma-P2P') do (
	set isValid=1
	echo #################################################################
	echo          Running Testcase - %%B
	echo #################################################################
	REM Loading the Env
	set INIT_FILE=\%%A
	init\InitTestEnv.exe %1
	REM C:\python25\python InitTestEnv.py %1
	wfa_ucc.exe 1 %%A %%B
	REM C:\python25\python wfa_ucc.py 1 %%A %%B
	)
	IF NOT "%isValid%"=="1" echo Invalid Testcase Name - %1


GOTO EOF

:GROUP
IF "%2"=="" GOTO HELP

FOR /F  %%T in ('findstr "P2P" %2') do (
	FOR /F "eol=# tokens=2,3 delims=!" %%A in ('findstr /C:"%%T!" Sigma-P2P') do (
	set isValid="1"
	echo #################################################################
	echo          Running Testcase - %%T
	echo #################################################################
	REM Loading the Env
	set INIT_FILE=\%%A
	
	init\InitTestEnv.exe %%T
	REM C:\python25\python InitTestEnv.py %%T
	wfa_ucc.exe 1 %%A %%B
	REM C:\python25\python wfa_ucc.py 1 %%A %%B
	)
	IF "%isValid%"==1 echo Invalid Testcase Name - %%T
	set isValid=0
)


GOTO EOF

:HELP
echo "Usage - 'P2PTest <P2P Testcase Name>' "
echo "         For example, P2PTest P2P-4.1.1" 

:EOF
REM result.html