@echo off
cls
REM #################################################################
REM This batch file runs the UCC script for given 11n testcases Name
REM Usage - PMFTest <PMF Testcase Name>
REM #################################################################


REM Path for the UCC command files folder
set UCC_CMD_PATH=..\cmds\Sigma-PMF
set MASTER_XML_FILE=\MasterTestInfo.xml
set PROG_NAME=PMF
set isValid=
echo .
echo          Running Testcase - %1 * [Version V1-0-0-3 - PMF System Interoperability Test Plan]
echo .

del result.html

IF "%1"=="" GOTO HELP
IF "%1"=="group" GOTO GROUP

IF "%1"=="all" GOTO ALL
IF NOT "%1"=="all" GOTO SINGLE

:ALL
set searchString=11n
GOTO S
:SINGLE
set searchString=%1
GOTO S

:S
	FOR /F "eol=# tokens=2,3 delims=!" %%A in ('findstr "%searchString%!" Sigma-PMF') do (
	set isValid=1
	echo #################################################################
	echo          Running Testcase - %%B
	echo #################################################################
	REM Loading the Env
	set INIT_FILE=\%%A
	init\InitTestEnv.exe %1
	REM C:\python27\python InitTestEnv.py %1
	wfa_ucc.exe 1 %%A %%B
	REM C:\python27\python wfa_ucc.py 1 %%A %%B
	)
	IF NOT "%isValid%"=="1" echo Invalid Testcase Name - %1


GOTO EOF

:GROUP
IF "%2"=="" GOTO HELP
FOR /F  %%T in ('findstr "PMF" %2') do (
	FOR /F "eol=# tokens=2,3 delims=!" %%A in ('findstr /C:"%%T!" Sigma-PMF') do (
	set isValid="1"
	echo #################################################################
	echo          Running Testcase - %%T
	echo #################################################################
	REM Loading the Env
	set INIT_FILE=\%%A
        rem C:\python27\python InitTestEnv.py %%T
	init\InitTestEnv.exe %%T
	wfa_ucc.exe 1 %%A %%B
        rem C:\python27\python wfa_ucc.py 1 %%A %%B
	)
	IF "%isValid%"==1 echo Invalid Testcase Name - %%T
	set isValid=0
)


GOTO EOF

:HELP
echo "Usage - 'PMFTest <PMF Testcase Name>'  or"
echo "        'PMFTest group <file with list of test cases>'"

:EOF