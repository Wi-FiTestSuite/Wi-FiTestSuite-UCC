@echo off
cls
REM #################################################################
REM This batch file runs the UCC script for given WMM-AC testcases Name
REM Usage - WMM-ACTest <WMM-AC Testcase Name>
REM #################################################################


REM Path for the UCC command files folder
set UCC_CMD_PATH=..\..\cmds\Sigma-WMM-AC\11b
set MASTER_XML_FILE=MasterTestInfo.xml
set isValid=
echo .
echo          Running Testcase - %1 * [Version .54 - WMM-AC System Interoperability Test Plan]
echo .

del result.txt

IF "%1"=="" GOTO HELP
IF "%1"=="group" GOTO GROUP

IF "%1"=="all" GOTO ALL
IF NOT "%1"=="all" GOTO SINGLE

:ALL
set searchString=WMM-AC
GOTO S
:SINGLE
set searchString=%1
GOTO S

:S
	FOR /F "eol=# tokens=2,3 delims=!" %%A in ('findstr "%searchString%!" WMM-AC-Tests') do (
	set isValid=1
	echo #################################################################
	echo          Running Testcase - %%B
	echo #################################################################
	REM Loading the Env
	set INIT_FILE=\%%A
	REM C:\python26\python InitTestEnv.py %1
	REM wfa_ucc.exe 1 %%A %%B
	C:\python25\python wfa_ucc.py 1 %%A %%B
	)
	IF NOT "%isValid%"=="1" echo Invalid Testcase Name - %1


GOTO EOF

:GROUP
IF "%2"=="" GOTO HELP
FOR /F  %%T in ('findstr "AC" %2') do (
	FOR /F "eol=# tokens=2,3 delims=!" %%A in ('findstr /C:"%%T!" WMM-AC-Tests') do (
	set isValid="1"
	echo #################################################################
	echo          Running Testcase - %%T
	echo #################################################################
	REM Loading the Env
	set INIT_FILE=\%%A
	REM C:\python26\python InitTestEnv.py %%T
	REM wfa_ucc.exe 1 %%A %%B
	C:\python25\python wfa_ucc.py 1 %%A %%B
	)
	IF "%isValid%"==1 echo Invalid Testcase Name - %%T
	set isValid=0
)


GOTO EOF

:HELP
echo "Usage - 'WMM-ACTest <WMM-AC Testcase Name>'  or"
echo "        'WMM-ACTest all'  or"
echo "        'WMM-ACTest group <file with list of test cases>'"

:EOF
type result.txt