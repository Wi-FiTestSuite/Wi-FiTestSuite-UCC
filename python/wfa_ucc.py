###################################################################
#
# Copyright (c) 2014 Wi-Fi Alliance
#
# Permission to use, copy, modify, and/or distribute this software for any
# purpose with or without fee is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY
# SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER
# RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT,
# NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH THE
# USE OR PERFORMANCE OF THIS SOFTWARE.
#
###################################################################

#!/usr/bin/evn python
import os, sys
from myutils import tmsPrint
from myutils import tmsPacket
from myutils import scanner
from myutils import process_ipadd
from myutils import process_cmdfile
from myutils import firstword
from myutils import init_logging
from myutils import printStreamResults
from myutils import close_conn
from myutils import wfa_sys_exit
from myutils import setUCCPath
from myutils import reset
from myutils import wfa_print_result
from myutils import get_reset_default_file

from InitTestEnv import InitTestEnv
import logging
import time
import re
nargs = len(sys.argv)

class UCCTestConfig:
    def __init_(self, testID, cmdPath, progName, initFile, TBFile, QualAP="", QualSTA="", DUTName="", qual=0):
        self.cmdPath = cmdPath
        self.progName = progName
        self.initFile = initFile
        self.TBFile = TBFile
        self.testID = testID
        self.TB_QUAL_AP = QualAP
        self.TB_QUAL_STA = QualSTA
        self.DUT_NAME = ""
        self.qual = 0

    def __str__(self):
        return "\n Test ID = [%s] CmdPath = [%s] Prog Name = [%s] initFile =[%s] TBFile =[%s]" % (self.testID, self.cmdPath, self.progName, self.initFile, self.TBFile)

U = UCCTestConfig()
starttime = time.time()

def main():
    global U
    if (nargs < 3) or (sys.argv[2] == 'group' and nargs < 4):
        print 'Incorrect Command line !!! \n\rUSAGE : wfa_ucc <Program Name> <Test ID> OR wfa_ucc <Program Name> group <group file name>\
        \n\r [1] Program Name :   AC-11AG/AC-11B/AC-11N\
        \n\r                      HS2\
        \n\r                      HS2-R2\
        \n\r                      N\
        \n\r                      P2P\
        \n\r                      PMF\
        \n\r                      TDLS\
        \n\r                      WFD\
        \n\r                      WMM\
        \n\r                      WPA2\
        \n\r                      WFDS\
        \n\r                      VHT\
        \n\r                      60GHz\
        \n\r                      WPS\
        \n\r                      WMMPS\
        \n\r                      NAN\
        \n\r\n\r [2] Test ID : Test case ID for that program            OR\
        \n\r\n\r [2] group : group if running group of test cases followed by group file name\
        \n\r\n\r [3] group file name: Group file name which contains list of test cases\
        \n\r\n\r\
        \n\r        For example, To run test P2P-4.1.1 of P2P(Wi-Fi Direct) program,\
        \n\r\n\r    wfa_ucc P2P P2P-4.1.1        OR\
        \n\r        For example, To run group of P2P test cases listed in file L1.txt\
        \n\r\n\r    wfa_ucc P2P group L1.txt'
        return
    starttime = time.time()

    cmdPath = ReadMapFile("WTS-UCC.txt", "%s_CMD_PATH" %(sys.argv[1]), "=")
    tbAP = ReadMapFile("WTS-UCC.txt", "%s_TESTBED_AP" %(sys.argv[1]), "=")
    tests = ReadMapFile("WTS-UCC.txt", "%s_TEST_LIST" %(sys.argv[1]), "=")

    if cmdPath == -1 or tbAP == -1 or tests == -1:
        print "Invalid Program Name - %s" % sys.argv[1]
        return
    setattr(U, "cmdPath", cmdPath)
    setattr(U, "progName", sys.argv[1])
    setattr(U, "TBFile", tbAP)
    setattr(U, "qual", 0)
    setattr(U, "TB_QUAL_AP", "")
    setattr(U, "TB_QUAL_STA", "")
    setattr(U, "DUT_NAME", "")

    grp = 0

    if sys.argv[2] == "group":
        grpFile = sys.argv[3]
        if os.path.exists(grpFile) == 0:
            print "Invalid Group File -%s-" % grpFile
            return
        fileP = open(grpFile, 'r')
        for l in fileP.readlines():
            if not l:
                break
            setattr(U, "testID", l.strip())
            runTestCase(tests, U.testID, grp)
            grp = 1
        return

    if sys.argv[2] == "qual":
        qualFile = sys.argv[3]
        if os.path.exists(qualFile) == 0:
            print "Invalid Group File -%s-" % qualFile
            return
        U.qual = 1
        fileP = open(qualFile, 'r')
        for l in fileP.readlines():
            if not l:
                break
            if re.search("#", l):
                continue

            if re.search("DUT_NAME", l) or re.search("TB_QUAL_AP", l) or re.search("TB_QUAL_STA", l):
                l1 = l.split("=")

                if len(l1) > 1:
                    print "[%s][%s]" % (l1[0].strip(), l1[1].strip())
                    setattr(U, l1[0].strip(), l1[1].strip())

            if re.search("%s-" % sys.argv[1], l):
                # Run the test case

                setattr(U, "testID", l.strip())
                if U.DUT_NAME == "" or (U.TB_QUAL_AP == "" and U.TB_QUAL_STA == ""):
                    print "One or more parameters missing DUT[%s] AP[%s] STA[%s]" % (U.DUT_NAME, U.TB_QUAL_AP, U.TB_QUAL_STA)
                    exit(1)

                runTestCase(tests, U.testID, grp)
                grp = 1

    else:
        setattr(U, "testID", sys.argv[2])
        runTestCase(tests, U.testID)

    return

def runTestCase(testListFile, testID, grp=0):
    global U, starttime
    print "\n*** Running Test - %s *** \n" % testID

    initFile = ReadMapFile(testListFile, testID, "!")
    testFile = ReadMapFile(testListFile, testID, "!", 2)

    if initFile == -1 or testFile == -1:
        print "Invalid test case - %s" % testID
        exit(1)

    setattr(U, "initFile", initFile)

    #init Logging
    init_logging(U.testID, 1, grp)

    tmsPacket.ProgramName = U.progName
    tmsPacket.TestResult = "FAIL"
    tmsPrint()

    logging.info("\n Test Info %s" % U)

    uccPath = U.cmdPath
    if uccPath.endswith('\\') == 0:
        uccPath = uccPath + '\\'

    setUCCPath(uccPath)
    initFile = uccPath + initFile
    testFile = uccPath + testFile
    # Run Init Env
    if not re.search("WMM-", testID):
        if U.qual:
            InitTestEnv(U.testID, U.cmdPath, U.progName, U.initFile, U.TBFile, U.qual, U.TB_QUAL_AP, U.TB_QUAL_STA)
        else:
            InitTestEnv(U.testID, U.cmdPath, U.progName, U.initFile, U.TBFile)


    #Run UCC Core

    if os.path.exists(initFile) == 0:
        logging.error("Invalid file name - %s" % initFile)
        wfa_print_result("1")

    if os.path.exists(testFile) == 0:
        logging.error("Invalid file name - %s" % testFile)
        wfa_print_result("1")

    logging.info("\n %7s Testcase Init File = %s \n" % ("", initFile))
    logging.info("\n %7s Testcase Command File = %s \n" % ("", testFile))

    if U.qual:
        fileW = open("%s\DUTParam.txt" % (U.cmdPath), 'w')
        print "- DUT NAME [%s]" % U.DUT_NAME.lower()
        dut_ca = ReadMapFile(initFile, "wfa_control_agent_%s" % U.DUT_NAME.lower(), "!")

        # Following assumes that $Channel is the first parmater in InitEnv.txt
        channel = ReadMapFile("%s\InitEnv.txt" % U.cmdPath, "define", "!", 2)
        band = "24G"
        if int(channel) > 35:
            band = "5G"

        fileW.write("wfa_control_agent_dut!%s!\n" % dut_ca)
        fileW.write("define!$DUT_Name!%s!\n" % (U.DUT_NAME))

        fileW.write("define!$DutMacAddress!$%sMACAddress_%s!\n" % (U.DUT_NAME, band))

        fileW.write("define!$APUT_uname!%sUserName!\n" % (U.DUT_NAME))
        fileW.write("define!$APUT_pword!%sAPPassword!\n" % (U.DUT_NAME))
        fileW.write("define!$APUT_hostname!%sHostName!\n" % (U.DUT_NAME))
        fileW.close()

    logging.info("START: TEST CASE [%s] " % testID)
    try:
        expt_msg = ""
        fileInit = open(initFile)
        print "\n-------------------\n"
        scanner(fileInit, firstword)
        print "\n-------------------\n"
        process_cmdfile(testFile)

    except Exception:
        expt_msg = "%s" % sys.exc_info()[1]
    finally:  
        if expt_msg != "":
            if re.search("r_info", expt_msg):
                wfa_print_result(1)
            else:
                wfa_print_result(0, expt_msg)
        else:
            wfa_print_result(1)

        if tmsPacket.TestResult != "PASS" and re.search("60G", U.testID):
            logging.info("#####Resetting the devices to their 60GHz defaults.....#####")
            resetFile = get_reset_default_file()
            if resetFile is None:
                logging.info("Reset file not found, skip resetting.....")
            else:
                resetFile= uccPath + resetFile
                process_cmdfile(resetFile)
        logging.info("END: TEST CASE [%s] " % testID)
        elapsed = (time.time() - starttime)
        logging.info("END: TEST CASE [%s]        Execution Time [%s] seconds" % (testID, round(elapsed,2)))
        fileInit.close()
        reset()

def ReadMapFile(filename, index, delim, n=1):
    iCount = 1
    returnString = -1
    if os.path.exists(filename) == 0:
        print "File not found -%s-" % filename
        return -1
    fileP = open(filename, 'r')
    for l in fileP.readlines():
        if not l:
            break
        line = l.split('#')
        command = line[0].split(delim)
        if index in command:
            returnString = command[command.index(index)+n].strip()
            break

    fileP.close()
    return returnString

if __name__ == "__main__":
    main()
