@echo off
cls
REM #################################################################
REM This batch file runs the UCC script for given 11n testcases Name
REM Usage - 11nTest <11n Testcase Name>
REM #################################################################


REM Path for the UCC command files folder
set UCC_CMD_PATH=..\..\cmds\Sigma-11n
set MASTER_XML_FILE=\Qual-MasterTestInfo.xml
set isValid=
echo .
echo          Running Testcase - %1 * [Version 1.8 - 11n System Interoperability Test Plan]
echo .

del result.txt

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
	FOR /F "eol=# tokens=2,3 delims=!" %%A in ('findstr "%searchString%!" Qual-Sigma-11n') do (
	set isValid=1
	echo #################################################################
	echo          Running Testcase - %%B
	echo #################################################################
	REM Loading the Env
	set INIT_FILE=\%%A
	C:\python25\python InitTestEnv.py %1
	REM wfa_ucc.exe 1 %%A %%B
	C:\python25\python wfa_ucc.py 1 %%A %%B
	)
	IF NOT "%isValid%"=="1" echo Invalid Testcase Name - %1


GOTO EOF

:GROUP
IF "%2"=="" GOTO HELP
FOR /F  %%T in ('findstr "N" %2') do (
	FOR /F "eol=# tokens=2,3 delims=!" %%A in ('findstr /C:"%%T!" Qual-Sigma-11n') do (
	set isValid="1"
	echo #################################################################
	echo          Running Testcase - %%T
	echo #################################################################
	REM Loading the Env
	set INIT_FILE=\%%A
	C:\python25\python InitTestEnv.py %%T
	REM wfa_ucc.exe 1 %%A %%B
	C:\python25\python wfa_ucc.py 1 %%A %%B
	)
	IF "%isValid%"==1 echo Invalid Testcase Name - %%T
	set isValid=0
)


GOTO EOF

:HELP
echo "Usage - '11nTest <11n Testcase Name>'  or"
echo "        '11nTest all'  or"
echo "        '11nTest group <file with list of test cases>'"

:EOF
type result.txt