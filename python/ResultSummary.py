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
from socket import *
from select import select
import os, sys
import logging
import logging.handlers
import time
import xml.dom.minidom
import inspect
import re
import subprocess
import thread, Queue
import ctypes
import pprint
import HTML

from xml.dom.minidom import Document
from xml.dom.minidom import getDOMImplementation
from xml.dom.minidom import parse
from xml.dom.minidom import Node

# Other libs needed for binary packaging
try:
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
    from InitTestEnv import InitTestEnv
    from time import gmtime, strftime
    from XMLLogger import XMLLogger
except ImportError:
    print ""

# Override createElement:
class XMLDoc(Document):
    def createElement(self, tag, textNode=None):
        el = Document.createElement(self, "%s" % tag)
        el.doc = self
        if textNode:
            el.appendChild(self.createTextNode(textNode))
        return el

class TBDevice:
    def __init__(self, vendor, model, driver, os, WTSControlAgent):
        self.vendor = vendor
        self.model = model
        self.driver = driver
        self.os = os
        self.WTSControlAgent = WTSControlAgent
        self.verified = 0
        self.msg = ""

    def AddXMLNode(self, doc, parent, ver=0):
        device = doc.createElement("Device")
        parent.appendChild(device)

        device.appendChild(doc.createElement("Vendor", self.vendor))
        device.appendChild(doc.createElement("Model", self.model))
        device.appendChild(doc.createElement("Driver", self.driver))
        device.appendChild(doc.createElement("OS", self.os))
        device.appendChild(doc.createElement("WTSControlAgent", self.WTSControlAgent))

        #Check if verification node to be added
        if ver:
            logging.debug("TBDevice::AddXMLNode : ver")
            verification = doc.createElement("Verification")
            if self.verified:
                status = "OK"
            else:
                status = "Mismatch"

            verification.appendChild(doc.createElement("Status", status))
            verification.appendChild(doc.createElement("Message", self.msg))

            device.appendChild(verification)

    def compare(self, node):
        rc = 0
        if self.vendor.lower() != node.vendor.lower():
            rc = 0
        else:
            if self.model.lower() != node.model.lower():
                rc = ("%s\n Model - Expected:%s \n-OR-" % (self.msg, node.model))
            if self.driver.lower() != node.driver.lower():
                rc = ("%s\n Driver - Expected:%s \n-OR-" % (self.msg, node.driver))
            if self.WTSControlAgent.lower() != node.WTSControlAgent.lower():
                rc = ("%s\n WTS Control Agent Expected:%s \n-OR-" % (self.msg, node.WTSControlAgent))

            if rc:
                self.msg = rc
            else:
                self.verified = 1

        return rc
    def __str__(self):
        pass

class WTSComponent:
    def __init_(self, name, version="", others=""):
        self.name = name
        self.version = version
        self.others = others

    def AddXMLNode(self, doc, parent):
        WTS = doc.createElement("WTSComponent")
        parent.appendChild(WTS)

        WTS.appendChild(doc.createElement("Name", self.name))
        WTS.appendChild(doc.createElement("Version", self.version))
        WTS.appendChild(doc.createElement("Others", self.others))

    def __str__(self):
        pass

class LogFile:
    def __init__(self, name, signature):
        self.name = name
        self.signature = signature

    def __str__(self):
        pass

class ACCClient:
    def __init__(self, ipaddr, ipport):
        self.ipaddr = ipaddr
        self.ipport = ipport
        self.socket = 0
        self.info = ""

    def connect(self):
        addr = (self.ipaddr, int(self.ipport))
        self.socket = socket(AF_INET, SOCK_STREAM)
        logging.info("Opening connection with ACC module at %s %s" % addr)

        try:
            self.socket.connect(addr)
            time.sleep(2)
        except:
            exc_info = sys.exc_info()
            logging.error('Connection Error, IP = %s PORT = %s REASON = %s', self.ipaddr, self.ipport, exc_info[1])
            raise StandardError("")

    def verifySign(self, filename):
        logging.info("ACC Client: Verifying Signature for [%s]" % filename)
        verResult = 0

        if not self.socket:
            self.connect()

        cmd = "verify_signature,FileName,%s" % filename

        logging.info(">> ACC:%s" % cmd)

        status = self.socket.send(cmd)
        logging.info("SENT: %s Bytes" % status)
        status = self.socket.recv(1024)

        logging.info("<< ACC:%s" % status)

        if status:
            status = status.lower()
            ss = status.split(",")
            logging.debug(ss)
            if len(ss) < 3:
                logging.error("<< Invalid ACC response: %s" % status)

            logging.info("Sign result [%s] Sign file [%s]" % (ss[1], ss[3]))
            verResult = ss[1]

            if len(ss) > 4:
                self.info = "%s" % ss[5]

        else:
            logging.error("<< Invalid ACC response: %s" % status)

        return verResult

    def __str__(self):
        return "%s:%s [%s]" % (self.ipaddr, self.ipport, self.socket)

class TestCase:
    def __init__(self, testID, result, r1="", r2="", logfiles=[]):
        self.testID = testID
        self.result = result
        self.r1 = r1
        self.r2 = r2
        self.logfiles = []
        self.totalRun = 0
        self.nPass = 0
        self.nFail = 0
        self.nErr = 0
        self.type = ""
        self.optionalFeature = ""
        self.passLogFile = ""
        self.SignVerification = 0
        self.SignVerificationResult = 0

    def AddXMLNode(self, doc, parent):
        TestCase = doc.createElement("TestCase")
        parent.appendChild(TestCase)

        TestCase.appendChild(doc.createElement("TestID", self.testID))
        TestCase.appendChild(doc.createElement("Result", self.result))
        TestCase.appendChild(doc.createElement("R1", self.r1))
        TestCase.appendChild(doc.createElement("R2", self.r2))
        TestCase.appendChild(doc.createElement("LatestPassLogFile", self.passLogFile))

        #Signature verification
        logging.debug("Signature verification required ? [%s]" % self.SignVerification)

        if self.passLogFile:
            if self.passLogFile.startswith("./"):
                fullPathFile = ("%s\\%s" % (os.getcwd(), self.passLogFile.lstrip("./").replace("/", "\\")))
            else:
                fullPathFile = self.passLogFile

        # Verify signature if Sign Flag is ON and .asc signature file exists
        if self.passLogFile and int(self.SignVerification) and os.path.exists("%s.asc" % fullPathFile):
            logging.info("Verifying Signature for [%s]" % fullPathFile)
            self.SignVerificationResult = ACC.verifySign(fullPathFile)
            TestCase.appendChild(doc.createElement("SignVerificationInfo", "%s" % (ACC.info)))
        else:
            TestCase.appendChild(doc.createElement("SignVerificationInfoInfo", "NO sign verification"))

        TestCase.appendChild(doc.createElement("SignVerification", "%s" % (self.SignVerificationResult)))
        LogFiles = doc.createElement("LogFiles")

        for l in self.logfiles:
            LogFile = doc.createElement("LogFile")
            LogFile.appendChild(doc.createElement("Name", l.name))
            LogFile.appendChild(doc.createElement("Signature", l.signature))
            LogFiles.appendChild(LogFile)

        Stats = doc.createElement("Stats")
        TestCase.appendChild(Stats)
        Stats.appendChild(doc.createElement("TotalRun", "%s" % self.totalRun))
        Stats.appendChild(doc.createElement("TotalPASS", "%s" % self.nPass))
        Stats.appendChild(doc.createElement("TotalFAIL", "%s" % self.nFail))
        Stats.appendChild(doc.createElement("TotalERROR", "%s" % self.nErr))
        TestCase.appendChild(LogFiles)

        TestCase.appendChild(doc.createElement("Type", self.type))

        if self.type == "Optional":
            TestCase.appendChild(doc.createElement("OptionalFeature", self.optionalFeature))

    def __str__(self):
        pass

class ResultSummary:
    def __init__(self, fileName, TestCriteriaFile, Prog, uid="", logpath="", mChk=1, stylesheet="Results-Format.xsl"):
        self.fileName = fileName
        self.TestResults = ""
        self.doc = XMLDoc()
        self.uid = uid
        self.logpath = logpath
        self.versionInfoFlag = 0
        self.testplanVersion = ""
        self.testplanID = ""
        self.sigKeyID = ""
        self.TestCases = []
        self.ProgramName = Prog
        self.TestCriteriaFile = xml.dom.minidom.parse(TestCriteriaFile)
        self.SignVerification = 0

        # Stylesheet
        self.doc.appendChild(self.doc.createProcessingInstruction("xml-stylesheet",
                             "type=\"text/xsl\" href=\"%s\"" % stylesheet))

        self.Results = self.doc.createElement("Results")
        self.Result = self.doc.createElement("Result")
        self.ResultInfo = self.doc.createElement("Info")
        self.TestResults = self.doc.createElement("TestResults")

        self.doc.appendChild(self.Results)
        self.Results.appendChild(self.Result)
        self.Result.appendChild(self.ResultInfo)
        self.Result.appendChild(self.TestResults)

        self.ResultInfo.appendChild(self.doc.createElement("ProgramName", self.ProgramName))
        self.ResultInfo.appendChild(self.doc.createElement("time", "%s" % time.strftime("%Y-%m-%dT%H:%M:%SZ", time.localtime())))
        self.ResultInfo.appendChild(self.doc.createElement("UID", self.uid))
        self.ResultInfo.appendChild(self.doc.createElement("TestplanVersion", self.testplanVersion))
        self.ResultInfo.appendChild(self.doc.createElement("TestCriteriaFileVersion", self.getAttrValue(self.TestCriteriaFile, "ConfigSets", "Version")))
        self.ResultInfo.appendChild(self.doc.createElement("TestplanID", self.testplanID))
        self.ResultInfo.appendChild(self.doc.createElement("SignatureKeyID", self.sigKeyID))

        self.mChk = int(mChk)

    def addVersionInfo(self, dlog):
        Testbed = getNodeHandle(dlog, ["Log", "Info", "Testbed"])

        # Add verified Testbed information in results summary
        vTestbed = self.doc.createElement("Testbed")

        if Testbed:
            # List of valid config sets from TestCriteriaFile
            tRight = getNodeHandle(self.TestCriteriaFile, ["ConfigSets", self.ProgramName, "ConfigSet"], "", 1)
            t = getNodeHandle(dlog, ["Log", "Info", "Testbed", "Device"], "", 1)

            if t:
                for tLeft in t:
                    l = self.compareTwoTBNodes(tLeft, tRight)
                    l.AddXMLNode(self.doc, vTestbed, 1)

                self.Result.appendChild(vTestbed)

        DUT = getNodeHandle(dlog, ["Log", "Info", "DUT"])
        if DUT:
            self.Result.appendChild(DUT)

        WTS = getNodeHandle(dlog, ["Log", "Info", "WTS"])
        if WTS:
            self.Result.appendChild(WTS)

        self.versionInfoFlag = 1

    def generateSummary(self):
        for f1 in os.listdir(self.logpath):
            logging.debug("Folder name [%s]" % f1)
            if f1.startswith(self.ProgramName):
                for f in os.listdir(self.logpath + "\\" + f1):
                    logging.debug("--File name [%s]" % f)
                    if f.endswith(".xml"):
                        lf = "%s%s/%s" % (self.logpath, f1, f)
                        logging.info("Processing log file - %s \n", lf)
                        try:
                            dlogFile = xml.dom.minidom.parse(lf)
                        except:
                            logging.debug("------------------------ Malformed file %s--" % f)
                            continue

                        if not self.versionInfoFlag:
                            self.addVersionInfo(dlogFile)
                        tID = self.getAttrValue(dlogFile, "Log", "id")
                        tID = tID.strip()
                        tResult = self.getNodeValue(dlogFile, "Log", "TestCaseResult")
                        sig = "1"

                        # Add result nodes to TestCase
                        if tID and tResult:
                            tResult = tResult.strip()
                            tList = ""
                            # check if test already present

                            for tList in self.TestCases:
                                if tList.testID == tID:
                                    break
                                logging.debug("-----------------[%s][%s]" % (tList.testID, tID))

                            # Always pick the latest PASS results
                            if tList == "" or tList.testID != tID:
                                t1 = TestCase(tID, tResult)
                                t1.passLogFile = lf
                                t1.SignVerification = self.SignVerification
                                self.TestCases.append(t1)
                                logging.debug("-----------------Appending[%s]" % (tID))
                            else:
                                t1 = tList

                            if tResult == "PASS" or tResult == "PASSED" or tResult == "COMPLETED":
                                t1.nPass = int(t1.nPass) + 1
                                t1.result = tResult
                                t1.passLogFile = lf

                            elif tResult == "FAILED" or tResult == "FAIL":
                                t1.nFail = int(t1.nFail) + 1
                            else:
                                #Check if manual check should be done
                                mchkInfo1 = self.getNodeValueloop(dlogFile, "Log", "ManualCheckInfo")
                                mchkInfo1 = mchkInfo1.split(",")
                                var = ""
                                for mchkInfo in mchkInfo1:
                                    if self.mChk and mchkInfo:
                                        os.startfile(self.logpath + "\\" + f1)
                                        var = raw_input("-Manual Analysis Needed- Test ID -[%s]\n %s \n\n-Enter the result [P or F]: " % (tID, mchkInfo))
                                        t1.result = var
                                        if var != "P":
                                            t1.nFail = int(t1.nFail) + 1
                                            t1.result = "FAILED (%s)" % mchkInfo
                                            break

                                    else:
                                        t1.nErr = int(t1.nErr) + 1
                                        break

                                if var == "P":
                                    t1.nPass = int(t1.nPass) + 1
                                    t1.result = "PASS"

                            t1.totalRun = t1.totalRun + 1

                            t1.logfiles.append(LogFile(lf, sig))

        testList = getNodeHandle(self.TestCriteriaFile, ["ConfigSets", self.ProgramName, "TestCases", "TestCase"], "", 1)
        for t in testList:
            listEmpty = 1
            for tList in self.TestCases:
                iTestFound = 0
                listEmpty = 0
                tID = self.getNodeValue(t, "TestCase", "TestID")
                tID = tID.strip()

                if tID == tList.testID:
                    logging.debug("----------------- MATCH[%s][%s]" % (tList.testID, tID))
                    printNode(t)
                    iTestFound = 1
                    tList.type = self.getNodeValue(t, "TestCase", "Type")
                    if tList.type == "Optional":
                        tList.optionalFeature = self.getNodeValue(t, "TestCase", "OptionalFeature")

                    tList.AddXMLNode(self.doc, self.TestResults)
                    break

            # If results not found for the test, mark it missing
            if not listEmpty and not iTestFound:
                tMissing = TestCase(tID, "NO Results Found")
                tMissing.type = self.getNodeValue(t, "TestCase", "Type")
                if tMissing.type == "Optional":
                    tMissing.optionalFeature = self.getNodeValue(t, "TestCase", "OptionalFeature")
                tMissing.AddXMLNode(self.doc, self.TestResults)

    def getAttrValue(self, node, tag, attr):
        """Return the first attribute value match"""
        for n in node.getElementsByTagName(tag):
            return n.attributes[attr].value

    def getNodeValue(self, node, tag, attr):
        """Return the first node value match"""
        for l in node.getElementsByTagName(attr):
            logging.debug(l)
            return l.firstChild.data

    def getNodeValueloop(self, node, tag, attr):
        """Return the first node value match"""
        val = ""
        for l in node.getElementsByTagName(attr):
            logging.debug(l)
            if val:
                val = "%s,%s" % (val, l.firstChild.data)
            else:
                val = "%s" % (l.firstChild.data)

        return val

    def getTBDeviceObject(self, node):
        """Convert all string to lower case for comparison"""
        lList = {}

        for n in node.getElementsByTagName("*"):
            if n.tagName:
                if hasattr(n.firstChild, 'data'):
                    lList.setdefault(n.tagName.strip(), n.firstChild.data.strip())
                else:
                    lList.setdefault(n.tagName.strip(), "")

        return TBDevice(lList["Vendor"], lList["Model"], lList["Driver"], lList["OS"], lList["WTSControlAgent"])

    def compareTwoTBNodes(self, left, right):
        logging.debug("TLeft = %s TRight = %s" % (left, right))

        lTBDevice = self.getTBDeviceObject(left)
        for r in right:
            rightList = getNodeHandle(r, ["ConfigSet", "Testbed", "Device"], r, 1)
            for d in rightList:
                rTBDevice = self.getTBDeviceObject(d)
                lTBDevice.compare(rTBDevice)
                if lTBDevice.verified: break
            if lTBDevice.verified: break

        if lTBDevice.verified == 0:
            logging.debug(lTBDevice.msg)

        return lTBDevice

    def writeXML(self):
        fXMLFile = open(self.fileName, "w")
        fXMLFile.write(self.doc.toprettyxml(indent=" "))
        fXMLFile.close()
        return

class ResultValidation:
    def __init__(self, SummaryFile, TestCriteriaFile, ProgramName):
        self.SummaryFile = xml.dom.minidom.parse(SummaryFile)
        self.TestCriteriaFile = xml.dom.minidom.parse(TestCriteriaFile)
        self.ProgramName = ProgramName
        self.result = "PASS"
        self.msgs = ["msg1", "msg2"]

        logging.debug("Summary File = %s TestCriteriaFile = %s" %(SummaryFile, TestCriteriaFile))

def printNode(node):
    for n in node.getElementsByTagName("*"):
        logging.debug("[%s]=[%s] " % (n.tagName.strip(), n.firstChild.data.strip()))

def _get_elements_by_tagName_helper(parent, name, rc):
    for node in parent.childNodes:
        if node.nodeType == Node.ELEMENT_NODE and (name == "*" or node.tagName == name):
            rc.append(node)

    return rc


def getNodeHandle(node, tagList, string="", lst=0):
    """Get the node handle for given depth of node name in tagList"""
    TagCounter = 0
    nHandle = []
    if string:
        node = xml.dom.minidom.parseString(string.toprettyxml(indent=" "))

    while TagCounter < len(tagList):
        nHandle = []
        _get_elements_by_tagName_helper(node, tagList[TagCounter], nHandle)

        logging.debug("Level = %s Element = %s Search %s"  % (TagCounter, nHandle, tagList[TagCounter]))
        if nHandle == []:
            break
        else:
            node = nHandle[0]

        TagCounter = TagCounter + 1

    #return the first match
    if nHandle:
        if lst:
            return nHandle
        else:
            return nHandle[0]
    return nHandle

def init_logging(_filename):
    logging.basicConfig(level=logging.DEBUG,
                        format='%(message)s',
                        datefmt='%a, %d %b %Y %H:%M:%S',
                        filename=_filename,
                        filemode='w')
    console = logging.StreamHandler()

    console.setLevel(logging.INFO)

    formatter = logging.Formatter('%(message)s')
    console.setFormatter(formatter)
    # add the handler to the root logger
    logging.getLogger('').addHandler(console)

    logging.info("###########################################################\n")
    logging.info('Debug log in file - %s' % (_filename))

def ReadMapFile(filename, index, delim, n=1):
    iCount = 1
    returnString = -1
    if os.path.exists(filename) == 0:
        print "File not found -%s-" % filename
        return -1
    fileP = open(filename, 'r')
    for l in fileP.readlines():
        if not l: break
        line = l.split('#')
        command = line[0].split(delim)
        if index in command:
            returnString = command[command.index(index)+n].strip()
            break

    fileP.close()
    return returnString

ACC = ""
def main():
    try:
        global ACC

        if nargs < 2:
            print "\n\rUSAGE : ResultSummary <Result Summary Config File> \n\r Result Summary Config File : See Sample Config File - WTS-ResultSummary.conf"
            return

        f = ReadMapFile(sys.argv[1], "OUTPUT_FILE", "=")
        if not f.endswith(".xml"):
            f = "%s.xml" % f

        sm = ReadMapFile(sys.argv[1], "M_CHECK", '=')
        log_path = ReadMapFile(sys.argv[1], "LOG_PATH", '=')

        if not log_path.endswith("/"):
            log_path = "%s/" % log_path

        prog_name = ReadMapFile(sys.argv[1], "PROG_NAME", '=')
        UID = ReadMapFile(sys.argv[1], "UID", '=')
        test_criteria = ReadMapFile(sys.argv[1], "TEST_CRITERIA_FILE", '=')
        format_style = ReadMapFile(sys.argv[1], "FORMAT_STYLE", '=')

        init_logging("debug-log-result-summary.txt")
        logging.info("LOG_PATH [%s] PROG_NAME [%s] UID [%s] OUTPUT_FILE [%s] TEST_CRITERIA_FILE [%s] FORMAT_STYLE [%s]"  % (log_path, prog_name, UID, f, test_criteria, format_style))

        if prog_name == '60G':
            prog_name = "_" + prog_name
        rSummary = ResultSummary(f, test_criteria, prog_name, UID, log_path, sm, format_style)

        signVerification = ReadMapFile(sys.argv[1], "SIGN_VERIFICATION", '=')

        # Enable Signature verification - by default it is disabled
        if signVerification == "1":
            setattr(rSummary, "SignVerification", 1)
            acc_ip = ReadMapFile(sys.argv[1], "ACC_IP_ADDR", '=')
            acc_port = ReadMapFile(sys.argv[1], "ACC_IP_PORT", '=')
            ACC = ACCClient(acc_ip, acc_port)
            #unit test with hard coded file name

        rSummary.generateSummary()
        rSummary.writeXML()

    except StandardError:
        err = sys.exc_info()
        logging.error("End %s" % err[1])

## Main
nargs = len(sys.argv)
if __name__ == "__main__":
    main()
