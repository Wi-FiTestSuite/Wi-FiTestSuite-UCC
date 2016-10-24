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

from __future__ import division
from socket import *
from time import gmtime, strftime
import thread, time, Queue, os
import sys, time
from select import select
import logging
import re
import ctypes
import random
import HTML
import json, io, re
import string
import xml.dom.minidom
import threading
from xml.dom.minidom import Document
from xml.dom.minidom import Node
from XMLLogger import XMLLogger
import math
from datetime import datetime
from random import randrange
from xml.dom.minidom import Node
from difflib import SequenceMatcher
VERSION = "9.2.0"


conntable = {}
retValueTable = {}
DisplayNameTable = {}
streamSendResultArray = []
streamRecvResultArray = []
streamInfoArray = []
streamInfoArrayTemp = []
lhs = []
rhs = []
oper = []
boolOp = []
oplist = []
runningPhase = '1'
testRunning = 0
threadCount = 0
resultPrinted = 0
ifcondBit = 1
ifCondBit = 1
iDNB = 0
iINV = 0
RTPCount = 1
socktimeout = 0
#default socket time out in seconds
deftimeout = 600
errdisplayed=0
thread_error_flag = False

#default command file path
MasterTestInfo="\MasterTestInfo.xml"
InitEnv = "\InitEnv.txt"
uccPath = '..\\..\\cmds'
DUTFeatureInfoFile = "./log/DUTFeatureInfo.html"
STATUS_CONST=('RUNNING','INVALID','ERROR','COMPLETE')
doc = ""

STD_INPUT_HANDLE = -10
STD_OUTPUT_HANDLE = -11
STD_ERROR_HANDLE = -12

FOREGROUND_BLUE = 0x01 # text color contains blue.
FOREGROUND_GREEN = 0x02 # text color contains green.
FOREGROUND_RED = 0x04 # text color contains red.
FOREGROUND_INTENSITY = 0x08 # text color is intensified.

#Define extra colours
FOREGROUND_WHITE = FOREGROUND_RED | FOREGROUND_BLUE | FOREGROUND_GREEN
FOREGROUND_YELLOW = FOREGROUND_RED | FOREGROUND_GREEN
FOREGROUND_CYAN	= FOREGROUND_BLUE | FOREGROUND_GREEN
FOREGROUND_MAGENTA = FOREGROUND_RED | FOREGROUND_BLUE
#FOREGROUND_WHITE = FOREGROUND_GREEN | FOREGROUND_RED --> this is yellow.

BACKGROUND_BLUE = 0x10 # background color contains blue.
BACKGROUND_GREEN = 0x20 # background color contains green.
BACKGROUND_RED = 0x40 # background color contains red.
BACKGROUND_INTENSITY = 0x80 # background color is intensified.

BACKGROUND_WHITE = BACKGROUND_RED | BACKGROUND_BLUE | BACKGROUND_GREEN
BACKGROUND_YELLOW = BACKGROUND_RED | BACKGROUND_GREEN
BACKGROUND_CYAN = BACKGROUND_BLUE | BACKGROUND_GREEN
BACKGROUND_MAGENTA = BACKGROUND_RED | BACKGROUND_BLUE

std_out_handle = ctypes.windll.kernel32.GetStdHandle(STD_OUTPUT_HANDLE)

#TMS response packet
class TMSResponse:

    #Init variables
    def __init__(self, TestResult="N/A", Mode="Sigma", DutParticipantName="Unknown", PrimaryTestbedParticipantName="Unknown" ):
        self.TmsEventId =""
        self.TestCaseId = ""
        self.Mode = Mode
        self.Dut = {'company':"", 'model':"", 'firmware':"", 'Category' : "", 'VendorDeviceId' : ""}
        self.PrimaryTestbed =  {'company':"", 'model':"", 'firmware':"", 'Category' : "", 'VendorDeviceId' : ""}
        self.SupplementalTestbeds = []
        self.TestResult = TestResult
        self.TimeStamp = ""
        self.LogFileName = ""
        self.ProgramName = ""
        self.DutParticipantName = DutParticipantName
        self.PrimaryTestbedParticipantName = PrimaryTestbedParticipantName

    def __str__(self):
        return("\n Test Event ID = [%s] Prog Name = [%s] Test Case = [%s] Dut Name =[%s] Model Number =[%s] Test Result =[%s]" % (self.TmsEventId,self.ProgramName,self.TestCaseId,self.dutName,self.dutModeNumber, self.testResult))
    
    #func to get class to dict
    def asDict(self):
        return self.__dict__

    def Search_MasterTestInfo(self, testID, tag):
        """
        Finds the value of given tag in master XML file of Testcase Info (from InitEnv)

        Parameters
        ----------
        testID : str
        tag : tuple of str

        Returns
        -------
        Tag Value (as per XML file) : str
        """
        global MasterTestInfo,doc,uccPath
        result=""

        doc = xml.dom.minidom.parse(uccPath + MasterTestInfo)

        for node in doc.getElementsByTagName(testID):
          L = node.getElementsByTagName(tag)
          for node2 in L:
              for node3 in node2.childNodes:
                  if node3.nodeType == Node.TEXT_NODE:
                      result = node3.nodeValue
                      return result

        return result

    def writeTMSJson(self, logLoc, logTime):
        """Write JSON for TMS -> grep log file and look for Version Info"""
        jsonFname="%s/tms_%s.json" %( logLoc , self.TestCaseId)
        convertedTime = time.strptime(logTime, "%b-%d-%Y__%H-%M-%S")
        self.TimeStamp = time.strftime('%Y-%m-%dT%H:%M:%SZ', convertedTime)
        try :
            primaryTB = self.Search_MasterTestInfo(self.TestCaseId, "PrimaryTestbed")
        except :
            #exception
            primaryTB ="n/a"

        BulkStorageServer = ""

        tmsPATH = './TmsClient.conf'
        if(os.path.isfile(tmsPATH)):
            with open(tmsPATH, "r") as f:
                for line in f:
                    if re.search(r"TmsEventId=", line):
                         pos = line.index('=') + 1
                         str = line[pos:].rstrip('\r\n')
                         self.TmsEventId = str

                    if re.search(r"TestbedParticipantName=", line):
                         pos = line.index('=') + 1
                         str = line[pos:].rstrip('\r\n')
                         if primaryTB != "" :
                            self.PrimaryTestbedParticipantName = str 
                         else: 
                            self.PrimaryTestbedParticipantName = ""

                    if re.search(r"DutParticipantName=", line):
                         pos = line.index('=') + 1
                         str = line[pos:].rstrip('\r\n')
                         self.DutParticipantName = str

                    if re.search(r"BulkStorageServer=", line):
                         pos = line.index('=') + 1
                         str = line[pos:].rstrip('\r\n')
                         BulkStorageServer = str

        if self.Dut.get('VendorDeviceId') != "":
            if self.PrimaryTestbed.get('VendorDeviceId') != "":
                self.LogFileName = BulkStorageServer + "/" + self.TmsEventId + "/" + self.Dut.get('VendorDeviceId') + "/" + self.PrimaryTestbed.get('VendorDeviceId') + "/" + self.TestCaseId + "/" + logTime + ".zip"
            else:
                self.LogFileName = BulkStorageServer + "/" + self.TmsEventId + "/" + self.Dut.get('VendorDeviceId') + "/" + self.TestCaseId + "/" + logTime + ".zip"
        else:
            self.LogFileName = BulkStorageServer + "/" + self.TmsEventId + "/" + self.TestCaseId + "/" + logTime + ".zip"

        tmsFile = open(jsonFname, "w")

        tmsDict = self.asDict()

        if primaryTB == "" :
            try:
                del tmsDict['PrimaryTestbed']
                del tmsDict['PrimaryTestbedParticipantName']
                del tmsDict['SupplementalTestbeds']
            except:
                logging.debug("primaryTB not found")
        else:
            try: 
                line = self.Search_MasterTestInfo(self.TestCaseId, "TB_LIST")
                tb_list = line.split(',')
                if len(tb_list) <= 1:
                    del tmsDict['SupplementalTestbeds']
            except:
                logging.debug("SupplimentalTestbeds not found")

        TmsFinalResult = {"TmsTestResult" : tmsDict}
        json.dump(TmsFinalResult, tmsFile, indent=4)

        tmsFile.close()

    #func to get device_get_info capi resonse
    def setDutDeviceInfo(self, displayname, response):
        category = self.Search_MasterTestInfo(self.TestCaseId, "DUT_CAT")
        dutName = ""
        dutModel = ""
        dutVersion = ""
        logging.debug("setDutDeviceInfo")

        specials = '$#&*()[]{};:,//<>?/\/|`~=+' #etc
        trans = string.maketrans(specials, '.'*len(specials))

        try:
            if re.search(r"vendor", response):
                posVendor = response.index('vendor,') + 7
                str = response[posVendor:]
                str = str.lstrip()
                try :
                    posSym = str.index(',')
                    dutName = str[:posSym]
                except :
                    dutName = str.rstrip('\n')

            if re.search(r"model", response):
                posVendor = response.index('model,') + 6
                str = response[posVendor:]
                str = str.lstrip()
                try:
                    posSym = str.index(',')
                    tempStr = str[:posSym]
                    dutModel = tempStr.translate(trans)
                except:
                    dutModel = str.rstrip('\n')
                    dutModel = dutModel.translate(trans)   

            if re.search(r"version", response):
                posVendor = response.index('version,') + 8
                str = response[posVendor:]
                str = str.lstrip()
                try :
                    posSym = str.index(',')
                    tempStr = str[:posSym]
                    dutVersion = tempStr.translate(trans)   
                except:
                    dutVersion = str.rstrip('\n')
                    dutVersion = dutVersion.translate(trans)   

        except:
            logging.info("couldn't create device info...")
            
                                               
        self.Dut['company'] = dutName
        self.Dut['model'] = dutModel
        self.Dut['firmware'] = dutVersion
        self.Dut['Category'] = category
        self.Dut['VendorDeviceId'] = dutName + "_" +  dutModel

    def setTestbedInfo(self, displayname, response):
        """To get device_get_info CAPI response"""
        primaryTB = ""
        try: 
            primaryTB = self.Search_MasterTestInfo(self.TestCaseId, "PrimaryTestbed")

            line = self.Search_MasterTestInfo(self.TestCaseId, "TB_LIST")
            if line == "":
                line = self.Search_MasterTestInfo(self.TestCaseId, "STA")
            
            tb_list = line.split(',')

            catline = self.Search_MasterTestInfo(self.TestCaseId, "TB_CAT")
            if catline == "":
                catline = self.Search_MasterTestInfo(self.TestCaseId, "STA_CAT")

            tb_category = catline.split(',')
        except: 
            logging.info("self.Search_MasterTestInfo error")

        #if there is no primary testbed then no need to create json..
        if primaryTB == "":
            logging.debug("no primary testbed info found")
            return
        #number of Stations and number of category should be matched..
        if len(tb_list) != len(tb_category):
            logging.info("num TB_LIST and TB_CAT doesn't match")
            return
        if len(tb_list) == 0:
            logging.info("num -- 0 ")
            return

        category  = ""
        primaryFlag = 0

        try:
            for index in range(len(tb_list)):

                str1 = tb_list[index].lower()
                str2 = displayname.lower()
                s = SequenceMatcher(None, str1, str2) 
                str3 = primaryTB.lower()
                
                if(s.ratio() >= 0.90):
                    category  = tb_category[index]
                    if str1 == str3 :
                        primaryFlag = 1

        except: 
            logging.info("error - sequence matcher...")
			
        #if there is no match, then skip
        if category == "" :
            return
        companyTestBed = ""
        modelTestBed = ""
        firmwareTestBed = ""

        specials = '$#&*()[]{};:,//<>?/\/|`~=+' #etc
        trans = string.maketrans(specials, '.'*len(specials))

        if re.search(r"status,COMPLETE", response):
            if re.search(r"vendor", response):
                posVendor = response.index('vendor,') + 7
                str = response[posVendor:]
                str = str.lstrip()
                try:
                    posSym = str.index(',')
                    companyTestBed = str[:posSym]
                except:
                    companyTestBed = str.rstrip('\n')
             
            if re.search(r"model", response):
                posVendor = response.index('model,') + 6
                str = response[posVendor:]
                str = str.lstrip()
                try:
                    posSym = str.index(',')
                    tempStr = str[:posSym]
                    modelTestBed = tempStr.translate(trans)   
                except:
                    modelTestBed = str.rstrip('\n')
                    modelTestBed = modelTestBed.translate(trans)  

            if re.search(r"version", response):
                posVendor = response.index('version,') + 8
                str = response[posVendor:]
                str = str.lstrip()
                try:
                    posSym = str.index(',')
                    tempStr = str[:posSym]
                    firmwareTestBed = tempStr.translate(trans)
                except:
                    firmwareTestBed = str.rstrip('\n')
                    firmwareTestBed = firmwareTestBed.translate(trans)

            if primaryFlag == 1:
                self.PrimaryTestbed['company'] = companyTestBed
                self.PrimaryTestbed['model'] = modelTestBed
                self.PrimaryTestbed['firmware'] = firmwareTestBed
                self.PrimaryTestbed['Category'] = category
                self.PrimaryTestbed['VendorDeviceId'] = companyTestBed + "_" +  modelTestBed

            else:
                self.SupplementalTestbeds.append({'company':companyTestBed, 'model':modelTestBed, 'firmware':firmwareTestBed, 'Category' : category, 'VendorDeviceId' : companyTestBed + "_" +  modelTestBed})                                                    

    def getTestID(self, pkgName):    
        
        taskID = pkgName    
        #removed first 6 digits of pkgName which is version of Sigma  ex) 8.1.0-NAN_Plugfest5
        self.TmsEventId = taskID[6:]

#global to save tms values
tmsPacket = TMSResponse()
tmsLogLocation = ""
tmsTimeStamp = ""

cSLog = ""
class classifiedLogs:
    """Global Handler for classified Logs"""
    def __init__(self, name, fileName, msg=""):
        self.name = name
        self.fileD = open(fileName, 'a')
        self.msg = msg
        self.fileD.write("%s\n" % msg)

    def log(self, msg):
        """Print out time and message into file"""
        self.fileD.write("%s | %s \n" %(time.strftime("%b:%d:%Y-%H:%M:%S",
                                                      time.localtime()), msg))
    def __str__(self):
        return "%s:%s" %(self.fileName, self.msg)
    def __del__(self):
        self.fileD.close()

class streamInfo:
    """Returns string in formatted stream info"""
    def __init__(self, streamID, IPAddress, pairID, direction,
                 trafficClass,frameRate,phase,RTPID,corrID):
        self.streamID = streamID
        self.IPAddress = IPAddress
        self.pairID = pairID
        self.direction = direction
        self.trafficClass = trafficClass
        self.frameRate = frameRate
        self.phase = phase
        self.status = -1
        self.RTPID = RTPID
        self.corrID = corrID
        self.streamTimeout = " "

    def __str__(self):
        return "%-10s Stream ID = %s , IP Address = %s \n\r%-10s pairID = %s direction = %s \n\r%-10s frameRate =%s \n\r%-10s status =%s  %s" % (' ', self.streamID, self.IPAddress, ' ', self.pairID, self.direction, ' ', self.frameRate, ' ', self.status, self.phase)


class streamResult:
    """Returns string in formatted stream result"""
    def __init__(self, streamID, IPAddress, rxFrames, txFrames, rxBytes,
                 txBytes, phase):
        self.streamID = streamID
        self.IPAddress = IPAddress
        self.rxFrames = rxFrames
        self.txFrames = txFrames
        self.rxBytes = rxBytes
        self.txBytes = txBytes
        self.phase = phase
    def __str__(self):
        return "%-10s RX   %10s  Bytes   |  TX  %10s   | Stream ID = %s" % (' ', self.rxBytes, self.txBytes, self.streamID)

class UCCThread (threading.Thread):
    def __init__(self, threadID, threadName, threadToAddr, threadCapiElem, command):
        threading.Thread.__init__(self)
        self.ID = threadID
        self.name = threadName
        self.toaddr = threadToAddr
        self.capi_elem = threadCapiElem
        self.command = command
    def run(self):
        global thread_error_flag
        try:
            logging.info("Starting %s" % self.name)
        # Get lock to synchronize threads
            logging.debug("To Addr:%s" % self.toaddr)
            if len(tstate) > 0:
                tstateStatus = tstateCheck(self.toaddr)
            tstate.append(self.toaddr)
            logging.debug("TstateAdd: %s" % tstate)
            status = send_capi_command(self.toaddr,self.capi_elem)
            process_resp(self.toaddr,status,self.capi_elem,self.command)
        # Free lock to release next thread
            tstate.remove(self.toaddr)
            logging.debug("TstateDel: %s" % tstate)
            logging.info("Exiting %s" % self.name)
        except:
            if thread_error_flag == False:
                thread_error_flag = True
# socket desc list to be used by select
waitsocks, readsocks, writesocks = [], [], []

#MTF init variables
tidx = 0
threadM = []
threads = []
tstate = []

#Multicast test
multicast = 0
tmp =0

def tstateCheck(toaddr):
    global tmp
    while 1:
        logging.debug("toaddr: %s tstate: %s" % (toaddr, tstate))
        if not toaddr in tstate:
            break
        time.sleep(0.1)
    return 1
	
def set_color(color, handle=std_out_handle):
    """(color) -> BOOL

    Example: set_color(FOREGROUND_GREEN | FOREGROUND_INTENSITY)
    """
    bool = ctypes.windll.kernel32.SetConsoleTextAttribute(handle, color)
    return bool

def setUCCPath(path):
    """Set absolute path of cmds or script location"""
    global uccPath
    uccPath = path
    return

def scanner(fileobject, linehandler):
    """Scan file objects"""
    for line in fileobject.readlines():
        if not line: break
        #logging.debug("%s" % line)
        linehandler(line)

def sock_tcp_conn(ipaddr, ipport):
    """function for client socket connection set to blocking mode"""
    global readsocks, waitsocks, deftimeout
    buf = 2048
    addr = (ipaddr, ipport)

    mysock = socket(AF_INET, SOCK_STREAM)
    # Temporarily commented. Will be tested on VHT test bed before deletion
    mysock.settimeout(deftimeout)
    try:
        mysock.connect(addr)
    except:
        exc_info = sys.exc_info()
        wfa_sys_exit("Control Network Timeout - IP-%s:%s REASON = %s" %(ipaddr,ipport,exc_info[1]))

    readsocks.append(mysock)
    # Add the descriptor to select wait
    waitsocks.append(mysock)
    return mysock

def process_ipadd(line, rc=0):
    """function to parse IP address and port number. Create socket connection if not already."""
    global conntable
    i = 0
    addrlist = []
    addrlist = line.split(':')
    naddr = len(addrlist)
    while i < naddr:
        ip = addrlist[i].split(',', 1)
        ipa = ip[0].split('=')[1]    # ip adress
        ipp = ip[1].split('=')[1]    # ip port

        if "%s:%s" %(ipa, ipp) in conntable and rc == 0:
            logging.info('Already Connected to - IP Addr = %s Port =%s', ipa, ipp)
            return
        logging.info('Connecting to - IP Addr = %s Port =%s', ipa, ipp)

        sockhdlr = sock_tcp_conn(ipa, int(ipp))
        conntable["%s:%s" %(ipa, ipp)] = sockhdlr
        i = i + 1

def close_conn():
    global conntable

def printStreamResults():
    """Determines if WMM or WPA2 before printing results"""
    global resultPrinted
    ProgName = os.getenv("PROG_NAME")
    if resultPrinted == 1:
        return

    if ProgName == "P2P":
        return
    if "WPA2Test" in retValueTable:
        logging.debug("WPA2 Results")
        printStreamResults_WPA2()
    else:
        printStreamResults_WMM()

def printStreamResults_WPA2():
    """Prints stream results of WPA2"""
    global resultPrinted
    maxRTP = 1
    set_color(FOREGROUND_WHITE)
    if not streamSendResultArray:
        resultPrinted = 0
    else:
        resultPrinted = 1
    logging.info("\n\r %-7s --------------------STREAM RESULTS-----------------------" % "")
    for s in streamSendResultArray:
        sDisplayAddress = s.IPAddress
        if s.IPAddress in DisplayNameTable:
            sDisplayAddress = DisplayNameTable[s.IPAddress]
        for r in streamInfoArray:
            if r.streamID == s.streamID and r.IPAddress == s.IPAddress and r.phase == s.phase:
                recv_id = r.pairID
                trafficClass = r.trafficClass
                phase = r.phase
                break
        for p in streamRecvResultArray:
            pDisplayAddress = p.IPAddress
            if p.IPAddress in DisplayNameTable:
                pDisplayAddress = DisplayNameTable[p.IPAddress]
            if p.streamID == recv_id and p.phase == s.phase:
                logging.info("\n\r %-7s -----  %s --> %s -----" %
                             ("", sDisplayAddress, pDisplayAddress))
                logging.info("\n%s" % s)
                if maxRTP < int(r.RTPID):
                    maxRTP = int(r.RTPID)
                logging.info("\n%s" % p)
                break
    set_color(FOREGROUND_WHITE)

def printStreamResults_WMM():
    """Prints stream results of WMM"""
    global resultPrinted
    summaryList = {}
    summaryStreamDisplay = {}
    maxRTP = 1
    i = 1
    recv_id = -1
    if not streamSendResultArray:
        resultPrinted = 0
    else:
        resultPrinted = 1
    logging.info("\n\r %-7s --------------------STREAM RESULTS-----------------------" % "")
    for s in streamSendResultArray:
        sDisplayAddress = s.IPAddress
        if s.IPAddress in DisplayNameTable:
            sDisplayAddress = DisplayNameTable[s.IPAddress]
        for r in streamInfoArray:
            if r.streamID == s.streamID and r.IPAddress == s.IPAddress and r.phase == s.phase:
                recv_id = r.pairID
                trafficClass = r.trafficClass
                phase = r.phase
                break
        for p in streamRecvResultArray:
            pDisplayAddress = p.IPAddress
            if p.IPAddress in DisplayNameTable:
                pDisplayAddress = DisplayNameTable[p.IPAddress]
            if p.streamID == recv_id and p.phase == s.phase:
                logging.info("\n\r %-7s ----- RTP_%s-%s ( %s --> %s ) PHASE  = %s -----" %("", r.RTPID, trafficClass, sDisplayAddress, pDisplayAddress, phase))
                logging.info("\n%s" % s)
                summaryList.setdefault("%s:%s"%(int(r.RTPID), int(phase)), p.rxBytes)
                summaryStreamDisplay.setdefault("%s:%s" % (int(r.RTPID), int(phase)), "RTP%-1s_%-10s [%s-->%s]" % (r.RTPID, trafficClass, sDisplayAddress, pDisplayAddress))
                if maxRTP < int(r.RTPID):
                    maxRTP = int(r.RTPID)
                logging.info("\n%s" % p)
                break
    set_color(FOREGROUND_WHITE)
    logging.info("--------------------------SUMMARY----------------------------------")
    logging.info(" %46s %10s | %10s" % ("|", "Phase1 (Bytes)", "Phase2 (Bytes)"))
    logging.info("-------------------------------------------------------------------")
    while i <= maxRTP:
        str1 = ""
        str2 = ""
        stremDisplay = ""
        if "%s:%s"%(i, "1") in summaryList:
            str1 = summaryList["%s:%s" % (i, "1")]
            stremDisplay = summaryStreamDisplay["%s:%s"%(i, "1")]
        if "%s:%s"%(i, "2") in summaryList:
            str2 = summaryList["%s:%s" % (i, "2")]
            stremDisplay = summaryStreamDisplay["%s:%s"%(i, "2")]

        logging.info("\n%6s %-43s %5s %10s | %10s" % (" ", stremDisplay, "|", str1, str2))
        i = i + 1
    set_color(FOREGROUND_INTENSITY)

def read1line(s):
    """To resolve a readline problem with multiple messages in one line"""
    ret = ''

    while True:
        try:
            c = s.recv(1)
        except OSError, e:
            logging.info("Recv error: " + e)
            print "Socket error " + e

        if c == '\n' or c == '':
            if c == '':
                logging.debug("get a null char")
            break
        else:
            ret += c

    return ret + '\n'

def responseWaitThreadFunc(_threadID, command, addr, receiverStream):
    """Thread runs until send string completion or when test stops running"""
    global waitsocks, readsocks, writesocks, runningPhase, testRunning, streamInfoArray, streamInfoArrayTemp, retValueTable
    if "$MT" in retValueTable:
        logging.info("MT START")
        while 1:
            if retValueTable["$MT"] == "0":
                break
            time.sleep(0.1)
        logging.info("MT STOP")

    sCounter1 = 0
    numOfSendStream = 0
    program_60G_flag = 0
    #for p in streamInfoArray:
    for p in streamInfoArrayTemp:
        if p.direction == 'send' or p.direction == 'receive':
            numOfSendStream += 1
    timeoutval = 180.0
    logging.debug("responseWaitThreadFunc started %s" % testRunning)
    start_time = time.time()
    while testRunning > 0:
        #Temporarily commented. Will be tested on VHT to confirm removal
        ######readables, writeables, exceptions = select(readsocks, writesocks, [],0.1)
        readables, writeables, exceptions = select(readsocks, [], [], timeoutval)
        if not readables:
            logging.info("DEBUG: 3 mins timeout caught")
            total_time = time.time() - start_time
            msg_string =  " Total wait time : " + str(total_time)
            testRunning = 0
            sendsock = conntable.get(addr)
            sendsock.shutdown(SHUT_RDWR)
            time.sleep(0.1)
            sendsock.close()
            #for p in streamInfoArray:
            for p in streamInfoArrayTemp:
                p.streamTimeout = "ABORTED Response timeout at " + str(addr) + msg_string
            break
        for sockobj in readables:
            if sockobj in waitsocks:
		        #Resolve the issue in reading 1 single line with multiple messages
                #resp = read1line(sockobj)
                
                dir_send_flag = 0
                try:
                    resp = read1line(sockobj)
                except IOError as e:
                    logging.info("IO error code: %s" % e.errno)
                    logging.info("IO error message: %s" % e.strerror)
                    #exc_info = sys.exc_info()
                    #wfa_sys_exit(exc_info[1])
                    testRunning = 0
                    sendsock = conntable.get(addr)
                    sendsock.shutdown(SHUT_RDWR)
                    time.sleep(0.1)
                    sendsock.close()
                    for p in streamInfoArrayTemp:
                        p.streamTimeout = "IO Error at " + str(addr) + e.strerror
                    break
                
                #resp_arr = resp.split(',')
                for socks in conntable:
                    if sockobj == conntable[socks]:
                        responseIPAddress = socks
                displayaddr = responseIPAddress
                if responseIPAddress in DisplayNameTable:
                    displayaddr = DisplayNameTable[responseIPAddress]
                    logging.info( "%-15s <--1 %s" % (displayaddr,resp))
                else:
                    logging.info("Response address not found")

                if not (re.search(STATUS_CONST[0], resp, re.I) or re.search(STATUS_CONST[1], resp, re.I) or re.search(STATUS_CONST[2], resp, re.I) or re.search(STATUS_CONST[3], resp, re.I)):
                    logging.debug("Receive error: expect <status,RUNNING|COMPLETE|INVALID|ERROR> but return - %s" % resp)
                    continue
                if re.search("RUNNING", resp):
                    #resp = resp.strip()
                    #resp = resp.lstrip('status,RUNNING')
                    #resp = resp.strip()
                    continue
                elif re.search("COMPLETE", resp):
                    logging.debug("Complete Returned")
                else:
                    #logging.info("Did not receive expected RUNNING or COMPLETE response, check device local log for additional information")
                    if re.search("ERROR", resp):
                        logging.info("Error Returned")
                    elif re.search("INVALID", resp):
                        logging.info("Invalid Returned")
                    p.status = 1
                    p.corrID = -1
                    #wfa_sys_exit(resp)
                    testRunning = 0
                    sendsock = conntable.get(addr)
                    sendsock.shutdown(SHUT_RDWR)
                    time.sleep(0.1)
                    sendsock.close()
                    for p in streamInfoArrayTemp:
                        p.streamTimeout = "Invalid Return at " + str(addr) + resp
                    break
                
                if re.search("txActFrames", resp):
                    program_60G_flag = 1

                resp = resp.strip()
                resp_arr = resp.split(',')
                logging.debug("%-15s <--2 %s" % (displayaddr, resp))
                # Check for send stream completion
                if len(resp_arr) > 2:
                    if resp_arr[3] == '':
                        logging.error("NULL streamID returned from %s" % responseIPAddress)
                        continue
                    if resp_arr[2] == 'streamID':
                        logging.debug("STREAM COMPLETED = %s" % (resp_arr[3]))

                        # spliting the values of multiple streams
                        idx = resp_arr[3].strip()
                        idx = idx.split(' ')
                        sCounter = 0 # For mutliple stream value returns
                        if program_60G_flag == 1:
                            if resp_arr[9].split(' ')[sCounter] == '' :
                                sCounter = 1
                        else:
                            if resp_arr[7].split(' ')[sCounter] == '' :
                                sCounter = 1
                        tmp_counter = sCounter
                        for i in idx:
                            if program_60G_flag == 1:
                                tmp_txFrames = resp_arr[7].split(' ')[tmp_counter]
                            else:
                                tmp_txFrames = resp_arr[5].split(' ')[tmp_counter]
                            if tmp_txFrames != '0':
                                dir_send_flag = 1
                            for p in streamInfoArrayTemp:
                                realID = p.streamID.split(';')[0]
                                if i == realID and p.direction == 'send':
                                    dir_send_flag = 1
                                    break
                            tmp_counter += 1

                        for i in idx:
#                                 txFrames = resp_arr[7].split(' ')[sCounter]
#                             logging.debug(" TXFRAMES = %s" % txFrames)
                            i = ("%s;%s"%(i, responseIPAddress))
                            if dir_send_flag == 1:
                                logging.info("%s (%-15s) <--  SEND Stream - %s Completed " % (displayaddr, responseIPAddress, i))

                                strmTimeStampList = []
                                for p in streamInfoArray:
                                    if p.IPAddress == responseIPAddress and p.streamID == i and p.phase == runningPhase:
                                        strmTimeStampList.append(p.corrID)
                                #for p in streamInfoArray:
                                for p in streamInfoArray:                                    
                                    if p.IPAddress == responseIPAddress and p.streamID == i and p.phase == runningPhase:
                                        if len(strmTimeStampList) > 1:
                                            p.corrID = -1
                                            p.status = 1
                                            strmTimeStampList.pop(0)
                                            continue
                                        else:
                                            p.corrID = -1
                                            p.status = 1
                                            break
                                if program_60G_flag == 1:
                                    streamSendResultArray.append(streamResult(i,responseIPAddress,resp_arr[9].split(' ')[sCounter],resp_arr[7].split(' ')[sCounter],resp_arr[13].split(' ')[sCounter],resp_arr[11].split(' ')[sCounter],runningPhase))
                                else:
                                    streamSendResultArray.append(streamResult(i,responseIPAddress,resp_arr[7].split(' ')[sCounter],resp_arr[5].split(' ')[sCounter],resp_arr[11].split(' ')[sCounter],resp_arr[9].split(' ')[sCounter],runningPhase))
                            else:
                                if program_60G_flag == 1:
                                    streamRecvResultArray.append(streamResult(i,responseIPAddress,resp_arr[9].split(' ')[sCounter],resp_arr[7].split(' ')[sCounter],resp_arr[13].split(' ')[sCounter],resp_arr[11].split(' ')[sCounter],runningPhase))
                                else:
                                    streamRecvResultArray.append(streamResult(i,responseIPAddress,resp_arr[7].split(' ')[sCounter],resp_arr[5].split(' ')[sCounter],resp_arr[11].split(' ')[sCounter],resp_arr[9].split(' ')[sCounter],runningPhase))
                                logging.info("%s (%-15s) <----  RECV Stream - %s Completed " % (displayaddr, responseIPAddress, i))

                            sCounter += 1
                            sCounter1+=1

                        program_60G_flag = 0
                        
                        if sCounter1 == numOfSendStream:
                            testRunning = 0
                            #sCounter1 = 0
                            #numOfSendStream = 0
                            #if program_60G_flag == 1:
                            streamInfoArrayTemp = []
            else:
                logging.debug('Unwanted data on socket')
    logging.debug("\n THREAD STOPPED ")
    return

def TimestampMillisec64():
    return int((datetime.utcnow() - datetime(1970, 1, 1)).total_seconds() * 1000)
def process_cmd(line):
    """
    Process CAPI commands and send through socket if necessary

    Parameters
    ----------
    line : str
        CAPI command followed by parameters with "," as delimiter

    Returns
    -------
    none

    Examples
    --------
	process_cmd(ca_get_version)
    process_cmd(sniffer_control_filter_capture,infile,_521-step1,
        outfile,521-step1_A,srcmac,00:11:22:33:44:55,
        destmac,55:44:33:22:11:00)
    """
    global conntable, threadCount, waitsocks_par, runningPhase, testRunning, streamInfoArray, streamInfoArrayTemp, resultPrinted
    global retValueTable, RTPCount, multicast, ifcondBit, iDNB, iINV, ifCondBit, tidx, socktimeout
    global tmsPacket
    line = line.rstrip()
    str = line.split('#')
    lhs = []
    rhs = []
    boolOp = []
    oper = []
    recv_id = {}

    try:
        if str[0] == '':
            return
        command = str[0].split('!')

        if "$MTF" in retValueTable and retValueTable["$MTF"] == "0":
            for t in threads:
                t.join()
        if thread_error_flag == True:
            wfa_sys_exit("Thread aborted")

        if command[0].lower() == "socktimeout":
            if int(command[1]) > 0:
                logging.info("Setting socket timeout=%d secs" % int(command[1]))
                socktimeout = int(command[1])
            else:
                logging.info("Resetting socket timeout")
                socktimeout = 0
            return
        if command[0].lower() == "else":
            if int(ifCondBit):
                ifCondBit = 0
            else:
                ifCondBit = 1
            return
        if command[0].lower() == "endif":
            ifCondBit = 1
            return
        if command[0].lower() == "if":
            itern = 0
            for count, val in enumerate(command):
                if count % 4 == 0:
                    itern = itern + 1
                    boolOp.append(val)
                elif count % 4 == 1:
                    lhs.append(val)
                elif count % 4 == 2:
                    oper.append(val)
                elif count % 4 == 3:
                    rhs.append(val)
            itern = itern - 1
            for iCount in range(0, itern):
                if lhs[iCount] in retValueTable:
                    lhs[iCount] = retValueTable[lhs[iCount]]
                if rhs[iCount] in retValueTable:
                    rhs[iCount] = retValueTable[rhs[iCount]]
                if(oper[iCount]).lower() == "=":
                    if lhs[iCount].lower() == rhs[iCount].lower():
                        ifcondBit = 1
                    else:
                        ifcondBit = 0
                elif (oper[iCount]).lower() == ">":
                    if float(lhs[iCount]) > float(rhs[iCount]):
                        ifcondBit = 1
                    else:
                        ifcondBit = 0
                elif (oper[iCount]).lower() == "<":
                    if float(lhs[iCount]) < float(rhs[iCount]):
                        ifcondBit = 1
                    else:
                        ifcondBit = 0
                elif (oper[iCount]).lower() == ">=":
                    if float(lhs[iCount]) >= float(rhs[iCount]):
                        ifcondBit = 1
                    else:
                        ifcondBit = 0
                elif (oper[iCount]).lower() == "<=":
                    if float(lhs[iCount]) <= float(rhs[iCount]):
                        ifcondBit = 1
                    else:
                        ifcondBit = 0
                elif (oper[iCount]).lower() == "<>":
                    if lhs[iCount].lower() != rhs[iCount].lower():
                        ifcondBit = 1
                    else:
                        ifcondBit = 0
                if boolOp[iCount] == "if":
                    ifCondBit = ifcondBit
                elif boolOp[iCount] == "or":
                    temp_or = ifcondBit
                    if ifCondBit or temp_or:
                        ifCondBit = 1
                    else:
                        ifCondBit = 0
                elif boolOp[iCount] == "and":
                    temp_and = ifcondBit
                    if ifCondBit and temp_and:
                        ifCondBit = 1
                    else:
                        ifCondBit = 0
                #return

        if int(ifCondBit) == 0:
            return

        if command[0].lower() == "mathexpr":
            myglobals = {}
            mylocals = {}
            tmp = command[1]
            dollarvarlist = re.findall(r'\$\w+',command[2])            
            mathstr = command[2].replace("$", "")
            for var in dollarvarlist:                
                if var in retValueTable:
                    nodollarvar = var.replace("$", "")                    
                    myglobals[nodollarvar] = float(retValueTable[var])
            for key,value in myglobals.iteritems():
                mathstr = mathstr.replace(key, "%s" % value)                

            try:                
                calrslt = eval(mathstr)
                print 'calrslt=%s' % calrslt
            except Exception as e:                
                logging.info('An error occurred : %s\n' % e)
                return
            retValueTable[tmp] = "%s" % float(calrslt)
        if command[0].lower() == "math":
            tmp = command[1]
            if command[1] in retValueTable:
                command[1] = retValueTable[command[1]]
            if command[3] in retValueTable:
                command[3] = retValueTable[command[3]]
            #Error handling for math operators, excluding rand
            if command[2].lower() != "rand":
                try:
                    vara = float(command[1])
                except ValueError:
                    print "You must enter a number"
                    set_color(FOREGROUND_RED | FOREGROUND_INTENSITY)
                    logging.info("Test Case Criteria Failure - You must enter a number")
                    set_color(FOREGROUND_INTENSITY)
                try:
                    varb = float(command[3])
                except ValueError:
                    print "You must enter a number"
                    set_color(FOREGROUND_RED | FOREGROUND_INTENSITY)
                    logging.info("Test Case Criteria Failure - You must enter a number")
                    set_color(FOREGROUND_INTENSITY)
            if(command[2]).lower() == "+":
                retValueTable[tmp] = "%s" % (float(command[1]) +  float(command[3]))
            if(command[2]).lower() == "-":
                retValueTable[tmp] = "%s" % (float(command[1]) -  float(command[3]))
            if(command[2]).lower() == "*":
                retValueTable[tmp] = "%s" % (float(command[1]) *  float(command[3]))
            if(command[2]).lower() == "/":
                retValueTable[tmp] = "%s" % (float(command[1]) /  float(command[3]))
            if(command[2]).lower() == "%":
                retValueTable[tmp] = "%s" % (int(command[1]) % int(command[3]))
            if command[2].lower() == "rand":
                #List of allowed values
                varlist = command[3].split(":")
                random_index = randrange(0, len(varlist))
                retValueTable[tmp] = "%s" % int(varlist[random_index])

        if command[0].lower() == "_dnb_":
            iDNB = 1
            return
        if command[0].lower() == "_inv":
            iINV = 1
            return
        if command[0].lower() == "inv_":
            iINV = 0
            return
        if command[0].lower() == "mexpr":
            if command[1] not in retValueTable:
                return
            if command[3] in retValueTable:
                command[3] = retValueTable[command[3]]
            if command[2] == "%":
                retValueTable[command[1]] = (int(retValueTable[command[1]]) * int(command[3])) / 100
            return
        if command[0].lower() == "cat":
            var = ""
            if len(command) < 5:
                logging.debug("Invalid CAT command")
            else:
                varlist = command[2].split(",")
                for v in varlist:
                    if v in retValueTable:
                        v = retValueTable[v]
                        if var:
                            var = ("%s%s%s" % (var, command[3], v))
                        else:
                            var = ("%s" % (v))

            logging.debug("VAR=[%s]" % var)

            if command[1] in retValueTable:
                retValueTable[command[1]] = var
            else:
                retValueTable.setdefault(command[1], var)

            return
        if command[0].lower() == "htoi":
            if command[1] in retValueTable:
                cmd1 = retValueTable[command[1]]
            else:
                cmd1 = command[1]
                
            if command[2] in retValueTable:
                cmd2 = retValueTable[command[2]]
            else:
                cmd2 = command[2]
            var = int("%s" % cmd1, 16)
            retValueTable[command[2]] = "%s" % var
            return

        if command[0].lower() == "reopen_conn":

            if command[1] in retValueTable:
                command[1] = retValueTable[command[1]]
            if command[2] in retValueTable:
                command[2] = retValueTable[command[2]]

            process_ipadd("ipaddr=%s, port=%s" % (command[1], command[2]), 1)
            return

        if command[0].lower() == "extract_p2p_ssid":
            if command[1] in retValueTable:
                command[1] = retValueTable[command[1]]
            p2p_ssid = command[1].split(' ')
            if len(p2p_ssid) > 1:
                retValueTable.setdefault("$P2P_SSID", "%s" % p2p_ssid[1])
            else:
                set_color(FOREGROUND_RED | FOREGROUND_INTENSITY)
                logging.info("Test Case Criteria Failure - Invalid P2P Group ID")
                set_color(FOREGROUND_INTENSITY)
                logging.error("Test Case Criteria Failure - Invalid P2P Group ID")
            return
        if command[0].lower() == "calculate_ext_listen_values":
            if command[1] not in retValueTable or command[2] not in retValueTable:
                wfa_sys_exit("Test Case Criteria Failure - %s or %s not available" % (command[1], command[2]))
            command[1] = retValueTable[command[1]]
            command[2] = retValueTable[command[2]]
            retValueTable.setdefault("$PROBE_REQ_INTERVAL", "%s" % (int(command[2]) / 2))
            retValueTable.setdefault("$PROBE_REQ_COUNT", "%s" % (int(command[1]) / (int(command[2]) / 2)))
            return
        if command[0].lower() == "get_rnd_ip_address":
            if command[1] in retValueTable:
                command[1] = retValueTable[command[1]]
            if command[2] in retValueTable:
                command[2] = retValueTable[command[2]]
            ip1 = command[1].split(".")
            ip2 = command[2].split(".")
            if (int(ip2[3]) + 1) != int(ip1[3]):
                rnd_ip = ("%s.%s.%s.%s" % (ip2[0], ip2[1], ip2[2], int(ip2[3]) + 1))
            else:
                rnd_ip = ("%s.%s.%s.%s" % (ip2[0], ip2[1], ip2[2], int(ip2[3]) + 2))
            retValueTable.setdefault(command[3], "%s" % rnd_ip)
            return

        if command[0].lower() == 'ucc_form_device_discovery_frame':
            iCn = 0
            for c in command:
                if iCn > 1 and c in command:
                    wfa_sys_exit("Invalid UCC command")
                    #command[1] Frame command[2] GOUT Device Address command[3] group ID command[4] Injector source Address command[5] Testbed Client address

            f = command[1].split('*')
            iCn = 0

            #Hex SSID
            SSID = retValueTable[command[3]].split(" ")[1]
            SSIDLength = len(SSID)
            SSIDLen1 = hex(int(SSIDLength) + 22).split("0x")[1]
            SSIDLen2 = "%s 00" % hex(int(SSIDLength + 6)).split("0x")[1]
            if int(len(SSIDLen2)) < 5:
                SSIDLen2 = "0%s" % SSIDLen2
            hexSSID = ""
            for s in SSID:
                h = hex(ord(s)).split("0x")[1]
                hexSSID = hexSSID + h
            logging.debug("hexSSID = %s hexLength %s" % (hexSSID, SSIDLength))
            FrameData = "%s%s%s%s%s%s%s%s%s%s%s%s" % (f[0],
                                                      retValueTable[command[2]],
                                                      retValueTable[command[4]],
                                                      retValueTable[command[2]],
                                                      f[3],
                                                      SSIDLen1,
                                                      f[4],
                                                      retValueTable[command[5]],
                                                      f[5],
                                                      SSIDLen2,
                                                      retValueTable[command[2]],
                                                      hexSSID)
            logging.debug (FrameData)
            retValueTable.setdefault("$INJECT_FRAME_DATA",FrameData)

        if command[0].lower() == 'addstaversioninfo':

            vInfo = command[1].split(",")
            i = 0

            if len(vInfo) < 5:
                logging.info("Incorrect version format")
                return

            if vInfo[0] not in retValueTable:
                logging.debug("Unknown Component[1] %s", vInfo[0])
                return

            if retValueTable[vInfo[0]] not in conntable:
                if retValueTable[retValueTable[vInfo[0]]] not in conntable:
                    logging.debug("Unknown Component[3] %s", vInfo[0])
                    return

            #print vInfo
            print len(retValueTable)
            for c in vInfo:
                if c in retValueTable:
                    vInfo[i] = retValueTable[c]
                if vInfo[i] in DisplayNameTable:
                    vInfo[i] = DisplayNameTable[vInfo[i]]
                i = i + 1
            XLogger.AddTestbedDevice(vInfo[1], vInfo[2], vInfo[3], vInfo[4])
            logging.debug(vInfo)
            return

        if command[0].lower() == 'adduccscriptversion':
            XLogger.AddWTSComponent("UCC", VERSION, command[1])

        if command[0].lower() == 'add_media_file':
            XLogger.addMediaLog(command[1])

        if command[0].lower() == 'manual_check_info':
            XLogger.setManualCheckInfo(command[1])

        if command[0].lower() == 'addwtscompversioninfo' or command[0].lower() == 'adddutversioninfo':

            vInfo = command[1].split(",")
            i = 0

            if len(vInfo) < 5:
                logging.info("Incorrect version format...")
                return

            if vInfo[0] in retValueTable:
                vInfo[0] = retValueTable[vInfo[0]]

            #print vInfo
            print len(retValueTable)
            for c in vInfo:
                if c in retValueTable:
                    vInfo[i] = retValueTable[c]
                if vInfo[i] in DisplayNameTable:
                    vInfo[i] = DisplayNameTable[vInfo[i]]
                i = i + 1

            if command[0].lower() == 'adddutversioninfo':
                XLogger.AddDUTInfo(vInfo[1], vInfo[2], vInfo[3], vInfo[4])
                logging.debug("DUT INFO [%s][%s][%s][%s]" % (vInfo[1], vInfo[2], vInfo[3], vInfo[4]))
            else:
                logging.debug("WTS Comp[%s][%s][%s][%s]" % (vInfo[1], vInfo[2], vInfo[3], vInfo[4]))
                XLogger.AddWTSComponent(vInfo[0], vInfo[1], "%s:%s:%s" % (vInfo[2], vInfo[3], vInfo[4]))

            logging.debug(vInfo)
            return

        if re.search('esultIBSS', command[0]):
            time.sleep(5)
            printStreamResults()
            process_passFailIBSS(command[1])
            return
        
        if re.search("STA", command[0]) or (re.search("AP", command[0]) and not re.search("TestbedAPConfigServer", command[0])) or re.search("SS",command[0]):
            if command[0] in retValueTable:
                command[0] = retValueTable[command[0]]
            else:
                return

        if re.search("wfa_tester", command[0]):
            if command[0] in retValueTable:
                command[0] = retValueTable[command[0]]
            else:
                return

        if command[0].lower() == 'exit':
            set_color(FOREGROUND_CYAN | FOREGROUND_INTENSITY)
            wfa_sys_exit("CAPI exit command - %s" % command[1])

        if command[0].lower() == 'pause':
            set_color(FOREGROUND_YELLOW | FOREGROUND_INTENSITY)
            logging.info("Exeuction Paused - %s \n Press any key to continue..." % command[1])
            sys.stdin.read(1)
            set_color(FOREGROUND_INTENSITY)
            return

        if command[0].lower() == 'sleep':
            if command[1] in retValueTable:
                command[1] = retValueTable[command[1]]
            time.sleep(float(command[1]))
            return
        if command[0].lower() == 'userinput':
            set_color(FOREGROUND_YELLOW | FOREGROUND_INTENSITY)
            logging.info("[USER INPUT REQUIRED]")
            udata = raw_input(command[1])
            if command[2] in retValueTable:
                retValueTable[command[2]] = udata
            else:
                retValueTable.setdefault(command[2], udata)

            set_color(FOREGROUND_INTENSITY)
            return
        if command[0].lower() == 'userinput_ifnowts':

            if retValueTable["$WTS_ControlAgent_Support"] == "0":
                set_color(FOREGROUND_YELLOW | FOREGROUND_INTENSITY)
                logging.info("[USER INPUT REQUIRED]")
                udata = raw_input(command[1])
                if command[2] in retValueTable:
                    retValueTable[command[2]] = udata
                else:
                    retValueTable.setdefault(command[2], udata)

                set_color(FOREGROUND_INTENSITY)
            return

        if command[0].lower() == 'ifnowts':

            if retValueTable["$WTS_ControlAgent_Support"] == "0":
                set_color(FOREGROUND_YELLOW | FOREGROUND_INTENSITY)
                if len(command) > 3 and command[2] in retValueTable:
                    s = "- %s" % retValueTable[command[2]]
                else:
                    s = ""
                logging.info("%s %s\n        Press any key to continue after done" % (command[1], s))

                sys.stdin.read(1)
                set_color(FOREGROUND_INTENSITY)

            return

        if command[0] == 'wfa_control_agent' or command[0] == 'wfa_control_agent_dut':
            capi_cmd=command[1].split(',')
            if retValueTable["$WTS_ControlAgent_Support"] == "0":
                if ("$WTS_TrafficAgent_Support" in retValueTable):
                    if "traffic_" not in capi_cmd[0]:
                        return
                else:
                    return

        if command[0].lower() == 'getuccsystemtime':
            timeStr = time.strftime("%H-%M-%S-%m-%d-%Y", time.localtime())
            logging.debug("\n Reading UCC System time %s" % timeStr)
            t = timeStr.split("-")
            retValueTable.setdefault("$month", t[3])
            retValueTable.setdefault("$date", t[4])
            retValueTable.setdefault("$year", t[5])
            retValueTable.setdefault("$hours", t[0])
            retValueTable.setdefault("$minutes", t[1])
            retValueTable.setdefault("$seconds", t[2])
            logging.debug("""\n UCC System Time- Month:%s: 
                                                Date:%s: 
                                                Year:%s: 
                                                Hours:%s: 
                                                Minutes:%s: 
                                                Seconds:%s:""" %
                                                (retValueTable["$month"],
                                                 retValueTable["$date"],
                                                 retValueTable["$year"],
                                                 retValueTable["$hours"],
                                                 retValueTable["$minutes"],
                                                 retValueTable["$seconds"]))
            return

        if command[0].lower() == 'r_info':
            rdata = "-"
            if command[1] in retValueTable:
                command[1] = retValueTable[command[1]]
            if len(command) > 1:
                rdata = command[2]
            resultPrinted = 1
            set_test_result(command[1], rdata, "-")
            wfa_sys_exit_0()
            return

        if command[0].lower() == 'info':
            set_color(FOREGROUND_CYAN | FOREGROUND_INTENSITY)
            if command[1] in retValueTable:
                command[1] = retValueTable[command[1]]
            logging.info("\n %7s ~~~~~ %s ~~~~~ \n" %("", command[1]))
            set_color(FOREGROUND_INTENSITY)
            return

        if re.search('define', command[0]):
            logging.debug("..Define %s = %s"%(command[1], command[2]))
            if command[1] in retValueTable:
                if command[2] in retValueTable:
                    command[2] = retValueTable[command[2]]
                retValueTable[command[1]] = command[2]
            else:
                if command[2] in retValueTable:
                    command[2] = retValueTable[command[2]]
                retValueTable.setdefault(command[1], command[2])

            return
        
        elif re.search('DisplayName',command[0]):
            if (command[1] in retValueTable):
                DisplayNameTable.setdefault(retValueTable[command[1]],command[2])
            else:
                DisplayNameTable.setdefault(command[1],command[2])
            return

        elif re.search('append', command[0]):
            cmd = command[2].split(" ")
            logging.debug("..append %s = %s %s using %s"%(command[1], cmd[0], cmd[1], command[3]))
            if command[1] in retValueTable:
                if cmd[0] in retValueTable:
                    cmd[0] = retValueTable[cmd[0]]
                if cmd[1] in retValueTable:
                    cmd[1] = retValueTable[cmd[1]]
                retValueTable[command[1]] = "%s%s%s" %(cmd[0], command[3], cmd[1])
            else:
                if cmd[0] in retValueTable:
                    cmd[0] = retValueTable[cmd[0]]
                if cmd[1] in retValueTable:
                    cmd[1] = retValueTable[cmd[1]]
                retValueTable.setdefault(command[1], "%s%s%s" %(cmd[0], command[3], cmd[1]))

            return

        elif command[0].lower() == 'getuserinput':

            set_color(FOREGROUND_YELLOW |FOREGROUND_INTENSITY)
            logging.info("[USER INPUT REQUIRED]")
            udata = raw_input(command[1])
            if command[2] in retValueTable:
                retValueTable[command[2]] = udata
            else:
                retValueTable.setdefault(command[2], udata)

            set_color(FOREGROUND_INTENSITY)
            return

        elif re.search('search', command[0]):
            if re.search('exact', command[4]):
                if command[1] in retValueTable:
                    cmd1 = retValueTable[command[1]]
                else:
                    cmd1 = command[1]

                if command[2] in retValueTable:
                    cmd2 = retValueTable[command[2]]
                else:
                    cmd2 = command[2]

                retValueTable[command[3]] = "0"
                if (sorted(cmd1) == sorted(cmd2)):
                    retValueTable[command[3]] = "1"

                return

            elif re.search('diff', command[4]):
                if command[1] in retValueTable:
                    cmd1 = retValueTable[command[1]]
                else:
                    cmd1 = command[1]

                if command[2] in retValueTable:
                    cmd2 = retValueTable[command[2]]
                else:
                    cmd2 = command[2]

                retValueTable[command[3]] = "0"
                if sorted(cmd1) == sorted(cmd2):
                    retValueTable[command[3]] = "1"
                else:
                    logging.debug("cmd1 %s, cmd2 %s" %(cmd1, cmd2))
                    cmd1 = set(cmd1.split(' '))
                    cmd2 = set(cmd2.split(' '))
                    cmd3 = cmd1.difference(cmd2)
                    logging.debug("Diff List %s" % cmd3)
                    retValueTable[command[3]] = "%s" %(' '.join(list(cmd3)))

                return

            elif re.search('substring', command[4]):
                if command[1] in retValueTable:
                    cmd1 = retValueTable[command[1]]
                else:
                    cmd1 = command[1]

                if command[2] in retValueTable:
                    cmd2 = retValueTable[command[2]]
                else:
                    cmd2 = command[2]

                retValueTable[command[3]] = "0"

                if cmd2 != "":
                    logging.info("Search \"%s\" in \"%s\"" %(cmd2, cmd1))
                    if (cmd1.find(cmd2) != -1):
                            retValueTable[command[3]] = "1"
            
                return

            else:
                if command[1] in retValueTable:
                    cmd1 = retValueTable[command[1]]
                else:
                    cmd1 = command[1]

                if command[2] in retValueTable:
                    cmd2 = retValueTable[command[2]].split(" ")
                else:
                    cmd2 = command[2].split(" ")

                retValueTable[command[3]] = "0"
                i = 0

                #Check for NULL before comparison
                if cmd2 != "":
                    for c in cmd2:
                        logging.info("Search \"%s\" in \"%s\"" %(cmd2[i], cmd1))
                        if re.search('%s' % cmd2[i], cmd1, re.IGNORECASE):
                            retValueTable[command[3]] = "1"
                        i += 1
            
                return

        elif re.search('generate_randnum', command[0]):
            logging.debug("In generate_randnum...")
            if re.search('null',command[1]):
                cmd1 = "null"
            else:
                if command[1] in retValueTable:
                    cmd1 = retValueTable[command[1]].split(" ")
                else:
                    cmd1 = command[1].split(" ")

            retValueTable[command[2]] = "0"

            if command[3] in retValueTable:
                cmd3 = int(retValueTable[command[3]])
            else:
                cmd3 = int(command[3])

            i = 0
            while True:
                randnum = random.randint(0, 65535)
                for c in cmd1:
                    if isinstance(c, int):
                        if(randnum == int(c)):
                            del randnum
                            break
                try:
                    oplist.append(randnum)
                    i = i + 1
                except NameError:
                    logging.debug("Not defined")
                if (i == cmd3):
                    break

            retValueTable[command[2]] = ' '.join("%d" % x for x in oplist)
            logging.debug(" %s" % retValueTable[command[2]])
            oplist = []

            return

        elif command[0].lower() == 'echo':
            set_color(FOREGROUND_YELLOW |FOREGROUND_INTENSITY)
            if command[1] in  retValueTable:
                logging.info("%s=%s" % (command[1], retValueTable[command[1]]))
            else:
                logging.info("Unknown variable %s" %command[1])
            set_color(FOREGROUND_INTENSITY)
            return
        elif command[0].lower() == 'echo_ifnowts' and retValueTable["$WTS_ControlAgent_Support"] == "0":
            set_color(FOREGROUND_BLUE |FOREGROUND_INTENSITY)
            if command[1] in  retValueTable:
                logging.info("-%s=%s-" % (command[1], retValueTable[command[1]]))
            else:
                logging.info("%s" % command[1])
            return

        elif command[0].lower() == 'storethroughput':
            cmd = command[2].split(",")
            logging.debug("Storing the Throughput(Mbps) value of stream %s[%s %s] in %s  duration=%s p=%s", cmd[0], cmd[3], "%", command[1], retValueTable[cmd[2]], cmd[1])
            P1 = -1
            strmTimeStampList2 = []
            for p in streamRecvResultArray:
                if p.streamID == retValueTable[cmd[0]] and int(p.phase) == int(cmd[1]):
                    strmTimeStampList2.append(p.streamID)
            logging.info("strmTimeStampList2 count %s" % len(strmTimeStampList2))
            for p in streamRecvResultArray:
                if p.streamID == retValueTable[cmd[0]] and int (p.phase) == int (cmd[1]):
                    if len(strmTimeStampList2) > 1:
                        strmTimeStampList2.pop(0)
                        continue
                    P1 = p.rxBytes
                    P1 = int(int(P1) / 100) * int(cmd[3])
                    if cmd[2] in retValueTable:
                        P1 = ((float(P1) * 8)) / (1000000 * int(retValueTable[cmd[2]]))
                    else:
                        P1 = ((float(P1) * 8)) / (1000000 * int(cmd[2]))
                    break
            logging.info("Storing %s = %s [Mbps]", command[1], P1)
            if command[1] in retValueTable:
                retValueTable[command[1]] = P1
            else:
                retValueTable.setdefault(command[1], P1)
            return

        elif command[0].lower() == 'resultwmm':
            time.sleep(5)
            printStreamResults()
            process_passFailWMM(command[1])
            return
        elif command[0].lower() == 'resultwmm_1':
            time.sleep(5)
            printStreamResults()
            process_passFailWMM_1(command[1])
            return
        elif command[0].lower() == 'resultwmm_2':
            time.sleep(5)
            printStreamResults()
            process_passFailWMM_2(command[1])
            return
        elif command[0].lower() == 'config_multi_subresults':
            time.sleep(5)
            process_config_multi_subresults(command[1])
            return
        elif re.search('CheckThroughput', command[0]):
            time.sleep(5)
            printStreamResults()
            process_CheckThroughput(command[1], 0)
            return
        elif re.search('CheckMCSThroughput', command[0]):
            time.sleep(5)
            printStreamResults()
            process_CheckMCSThroughput(command[1])
            return
        elif re.search('CheckDT4Result', command[0]):
            time.sleep(5)
            printStreamResults()
            process_CheckDT4(command[1])
            return
        elif re.search('TransactionThroughput', command[0]):
            time.sleep(5)
            printStreamResults()
            process_CheckThroughput(command[1], 1)
            return
        # Remove R from ResultCheck as some scripts might be case Sensitive
        elif re.search('esultCheck', command[0]):
            time.sleep(5)
            process_ResultCheck(command[1])
            return

        logging.debug("COMMAND - to %s" % command[0])
        if command[0] == 'wfa_test_commands':
            if command[1] in retValueTable:
                command[1] = retValueTable[command[1]]
            process_cmdfile("%s%s"%(uccPath, command[1]))
            return
        if command[0] == 'Phase':
            RTPCount = 1
            time.sleep(3)
            logging.debug("Starting Phase - %s ..." % command[1])
            runningPhase = command[1]
            threadCount = 0
            testRunning = 0
            time.sleep(2)
            return
        if len(command) < 3:
            set_color(FOREGROUND_RED | FOREGROUND_INTENSITY)
            logging.info("Test Case Criteria Failure - Incorrect format of line - %s",line)
            set_color(FOREGROUND_INTENSITY)
            logging.error('Test Case Criteria Failure - Incorrect format of line - %s',line)
            return

        ret_data_def = command[2]
        ret_data_def_type = ret_data_def.split(',')
        logging.debug("Command Return Type = %s" % (ret_data_def_type[0].lower()))
        if ret_data_def_type[0] == 'STREAMID' or ret_data_def_type[0] == 'INTERFACEID' or ret_data_def_type[0] == 'PING':
            ret_data_idx = ret_data_def_type[1]
        elif ret_data_def_type[0] == 'RECV_ID':
            recv_value = ret_data_def_type[1].split(' ')
            i = 0
            for r in recv_value:
                recv_id[i] = r
                i += 1
            logging.debug('RECV ID %s', recv_id)

        elif ret_data_def_type[0] == 'FILENAME':
            upload_file_desc = open(ret_data_def_type[1], 'a')
            logging.info('File desc=  %s', upload_file_desc)
            logging.info('Uploading to file -  %s', ret_data_def_type[1])

        if command[0] in retValueTable:
            toaddr = retValueTable[command[0]]
        else:
            return

        displayName = get_display_name(toaddr)

        capi_run = command[1].strip( )
        capi_elem = command[1].split(',')
        logging.debug("%s (%-15s) --> %s " % (displayName, toaddr, capi_elem))

        if capi_elem[0] == 'traffic_agent_receive_stop':
            idx = capi_elem.index('streamID')
            # Wait for Send to finish, in case of receive_stop
            sid = capi_elem[2].split(' ')
            capi_elem[idx+1] = ''
            for i in sid:
                val = retValueTable[i]
                if re.search(";", retValueTable[i]):
                    val = retValueTable[i].split(";")[0]

                #60GHz
                strmTimeStampList1 = []
                for p in streamInfoArray:
                    if p.pairID == retValueTable[i] and p.phase == runningPhase:
                        strmTimeStampList1.append(p.corrID)
                for p in streamInfoArray:
                    if p.pairID == retValueTable[i] and p.phase == runningPhase:
                        if len(strmTimeStampList1) > 1:
                            if p.corrID == -1 and p.status == 1:
                                strmTimeStampList1.pop(0)
                                continue
                        while p.corrID != -1 and p.status != 1:                            
                            #Minor sleep to avoid 100% CPU Usage by rapid while
                            if (p.streamTimeout != " "): #timeoutflag == 1:
                                wfa_sys_exit(p.streamTimeout)
                            time.sleep(0.5)

                        if multicast == 1:
                            capi_elem[idx+1] = val
                            break
                        else:
                            capi_elem[idx+1] += val
                            capi_elem[idx+1] += ' '
                            break
                    elif multicast == 1:
                        capi_elem[idx+1] = val

            capi_run = ','.join(capi_elem)
            capi_cmd = capi_run + ' \r\n'
            logging.info("%s (%-10s) --> %s" % (displayName, toaddr, capi_cmd))
            asock = conntable.get(toaddr)
            asock.send(capi_cmd)
            time.sleep(15)
            return

        elif capi_elem[0] == 'traffic_agent_send':
            idx = capi_elem.index('streamID')
            sid = capi_elem[2].split(' ')
            capi_elem[idx+1] = ''
            rCounter = 0
            for i in sid:
                #Making Send-receive Pair
                for s in streamInfoArray:
                    if s.IPAddress == toaddr and s.streamID == retValueTable[i] and s.phase == runningPhase:
                        s.pairID = retValueTable[recv_id[rCounter]]
                for s in streamInfoArray:
                    if s.IPAddress == toaddr and s.streamID == retValueTable[i] and s.phase == runningPhase:
                        s.pairID = retValueTable[recv_id[rCounter]]
                if re.search(";", retValueTable[i]):
                    val = retValueTable[i].split(";")[0]
                else:
                    val = retValueTable[i]
                capi_elem[idx+1] += val
                capi_elem[idx+1] += ' '
                rCounter += 1

            capi_run = ','.join(capi_elem)
            logging.info("%s (%-15s) --> %s " %(displayName, toaddr, capi_run))

            # Pass the receiver ID for send stream

            # Start the response wait thread (only once)
            if threadCount == 0:
                testRunning = 1
                thread.start_new(responseWaitThreadFunc, (threadCount, capi_run, toaddr, recv_id))
                threadCount = threadCount + 1
				#Temporary Addition for VHT
            capi_cmd = capi_run + ' \r\n'
            asock = conntable.get(toaddr)
            asock.send(capi_cmd)
            return
        elif capi_elem[0] == 'sniffer_inject_frame':
            elementCounter = 0
            newframe = ""
            for capiElem in capi_elem:
                if capiElem.lower() == "framedata":
                    frame = capi_elem[elementCounter+1].split(" ")
                    for fdata in frame:
                        if fdata in retValueTable:
                            fdata = retValueTable[fdata]
                        newframe = newframe+ ' ' + fdata
                    logging.debug("Inject Frame Data %s" % newframe)
                    capi_elem[elementCounter+1] = newframe
                    break
                elementCounter += 1

        else:
            if capi_elem[0] == 'sniffer_control_stop':
                time.sleep(2)
                testRunning = 0
                time.sleep(2)

            #Replacing the placeholder(s) in command.
            for id in retValueTable:
                elementCounter = 0
                for capiElem in capi_elem:

                    if capiElem == id:
                        if re.search(";", retValueTable[id]):
                            val = retValueTable[id].split(";")[0]
                        else:
                            val = retValueTable[id]
                        capi_elem[elementCounter] = val
                        logging.debug("Replacing the placeholder %s %s" % (id, capi_elem[elementCounter]))
                    elementCounter += 1

        if capi_elem[0] == 'sta_up_load':
            seq_no = 1
            code_no = 1
            while code_no != '0':
                capi_elem[3] = "%s" % seq_no
                seq_no += 1
                status = send_capi_command(toaddr, capi_elem)
                ss = status.rstrip('\r\n')
                logging.debug("%s (%s) <--- %s" % (displayName, toaddr, ss))
                stitems = ss.split(',')
                if  stitems[1] == "COMPLETE"  and len(stitems) > 3:
                    upload_file_desc.write(stitems[4])
                    code_no = stitems[3]

            upload_file_desc.close()
            return
        elif "$MTF" in retValueTable and iDNB == 0:
                if retValueTable["$MTF"] == "1":
                    # Create new thread
                    threadM.append(UCCThread(tidx, "Thread-%d" % tidx,toaddr, capi_elem,command))
                    threads.append(threadM[tidx])
                    # Start new thread
                    threadM[tidx].start()

                    tidx = tidx + 1
                    return
                else:
                    # Wait for all threads to complete
                    logging.debug("Main Thread")
                    status = send_capi_command(toaddr, capi_elem)

        else:
            if capi_elem[0] == 'sta_is_connected':
                isConnectRetry = 0
                while isConnectRetry < 10:
                    isConnectRetry = isConnectRetry + 1
                    time.sleep(4)
                    status = send_capi_command(toaddr, capi_elem)
                    ss = status.rstrip('\r\n')
                    logging.info("%s (%-15s) <-- %s" % (displayName, toaddr, ss))
                    stitems = ss.split(',')
                    if  stitems[1] == "COMPLETE"  and len(stitems) > 3:
                        retValueTable.setdefault("$IS_CONNECTED", stitems[3])
                        if "PingInternalChk" in retValueTable:
                            if retValueTable["PingInternalChk"] == "0":
                                logging.debug("Skipping IS_CONNECTED check")
                                return
                            elif stitems[3] == '1':
                                return
                            else:
                                continue
                        else:
                            if stitems[3] == '1':
                                return
                            else:
                                continue
                wfa_sys_exit("Test Case Criteria Failure - NO ASSOCIATION -- Aborting the test")

            else :
                status = send_capi_command(toaddr, capi_elem)

        process_resp(toaddr, status, capi_elem, command)

    except:
        exc_info = sys.exc_info()[1]
        wfa_sys_exit("%s" % exc_info)

# For P2P-NFC 
def process_resp(toaddr, status, capi_elem, command):
        global conntable,threadCount, waitsocks_par, runningPhase, testRunning, streamInfoArray, streamInfoArrayTemp, resultPrinted
        global retValueTable, RTPCount , multicast, ifcondBit, iDNB, iINV, ifCondBit, tidx

        ret_data_def = command[2]
        ret_data_def_type = ret_data_def.split(',')
        if (ret_data_def_type[0] == 'STREAMID' or
            ret_data_def_type[0] == 'INTERFACEID' or 
            ret_data_def_type[0] == 'PING'):
            ret_data_idx = ret_data_def_type[1]

        ss = status.rstrip('\r\n')
        displayName = get_display_name(toaddr)
        logging.info("%s (%-15s) <-- %s" % (get_display_name(toaddr),toaddr,ss ))
        if not ss and "$MT" not in retValueTable:
            set_color(FOREGROUND_RED | FOREGROUND_INTENSITY)
            logging.info('Test Case Criteria Failure - Please check the following:')
            logging.info('	- WTS CA is returning empty string, please make sure CA is working properly')
            set_color(FOREGROUND_INTENSITY)
        #Exit in case of ERROR
        if (re.search('ERROR', ss) or re.search('INVALID', ss)) and (iDNB == 0 and iINV == 0):
            set_test_result("ERROR", "-", "Command returned Error")
            wfa_sys_exit("Test Case Criteria Failure - Command returned Error. Aborting the test")
        if capi_elem[0] == 'device_get_info':
            try :
                if command[0] == 'wfa_control_agent_dut' :
                    tmsPacket.setDutDeviceInfo(displayName, ss)
                else :
                    tmsPacket.setTestbedInfo(displayName, ss)
            except :
                logging.debug( "exception -- device_get_info capi call")
        if ss:
            stitems = ss.split(',')
            if len(stitems) > 3:
                if stitems[2] == 'streamID':

                #60GHz
                    corrID = TimestampMillisec64()
                    if capi_elem[4] == 'send':
                    #streamInfoArray.append(streamInfo("%s;%s" %(stitems[3],toaddr),toaddr,-1,'send',capi_elem[16],capi_elem[18],runningPhase,RTPCount))
                    #60GHz                    
                        streamInfoArray.append(streamInfo("%s;%s" %(stitems[3],toaddr),toaddr,-1,'send',capi_elem[16],capi_elem[18],runningPhase,RTPCount,corrID))
                        streamInfoArrayTemp.append(streamInfo("%s;%s" %(stitems[3],toaddr),toaddr,-1,'send',capi_elem[16],capi_elem[18],runningPhase,RTPCount,corrID))
                        RTPCount = RTPCount + 1
                #else:
                    if capi_elem[4] == 'receive':
                    #streamInfoArray.append(streamInfo("%s;%s" %(stitems[3],toaddr),toaddr,-1,'receive',-1,-1,runningPhase,-1))
                        streamInfoArray.append(streamInfo("%s;%s" %(stitems[3],toaddr),toaddr,-1,'receive',-1,-1,runningPhase,-1,corrID))
                        streamInfoArrayTemp.append(streamInfo("%s;%s" %(stitems[3],toaddr),toaddr,-1,'receive',-1,-1,runningPhase,-1,corrID))
                    if capi_elem[2] == 'Multicast':
                        logging.debug("----MULTICAST----")
                        multicast = 1
                    if ret_data_idx in retValueTable:
                        retValueTable[ret_data_idx] = ("%s;%s" %(stitems[3], toaddr))
                    else:
                        retValueTable.setdefault(ret_data_idx, "%s;%s" %(stitems[3], toaddr))
                elif stitems[2] == 'interfaceType':
                    if ret_data_idx in retValueTable:
                        retValueTable[ret_data_idx] = ("%s" %(stitems[5]))
                    else:
                        retValueTable.setdefault(ret_data_idx, stitems[5])
                elif stitems[2].lower() == 'interfaceid':
                    if ret_data_idx in retValueTable:
                        retValueTable[ret_data_idx] = stitems[3].split('_')[0]
                    else:
                        retValueTable.setdefault(ret_data_idx, stitems[3].split('_')[0])
                elif capi_elem[0] == 'traffic_stop_ping':
                    retValueTable["%s;%s"%(capi_elem[2], toaddr)] = stitems[5]
                    logging.debug("%s = %s" %  (capi_elem[2], retValueTable["%s;%s"%(capi_elem[2], toaddr)]))
                    retValueTable["$pingResp"] = retValueTable["%s;%s"%(capi_elem[2], toaddr)]
                    if "PingInternalChk" in retValueTable:
                        if retValueTable["PingInternalChk"] == "0":
                            logging.debug("Ping Internal Check")
                        elif stitems[5] == '0':
                            wfa_sys_exit("Test Case Criteria Failure - NO IP Connection -- Aborting the test")
                    else:
                        if stitems[5] == '0':
                            wfa_sys_exit("Test Case Criteria Failure - NO IP Connection -- Aborting the test")
                if ret_data_def_type[0].lower() == "id":
                    i = 0

                    for s in stitems:
                        if(int(i)%2 == 0) and len(stitems) > i+1 and len(ret_data_def_type) > int(i/2):
                            logging.debug("--------> Adding %s = %s"%(ret_data_def_type[int(i/2)], stitems[i+1]))
                            stitems[i+1] = stitems[i+1].lstrip()
                            stitems[i+1] = stitems[i+1].rstrip(' ')
                            stitems[i+1] = stitems[i+1].rstrip('\n')
                            stitems[i+1] = stitems[i+1].rstrip('\r')
                            if ret_data_def_type[int(i/2)] in retValueTable:
                                retValueTable[ret_data_def_type[int(i/2)]] = stitems[i+1]
                            else:
                                retValueTable.setdefault(ret_data_def_type[int(i/2)], stitems[i+1])

                        i = int(i) + 1

            elif not re.search("COMPLETE", stitems[1]) and iINV == 0 and iDNB == 0:
                logging.info('COMPLETE not found in command %s' % command[1].strip())
        else:
            logging.info('Command %s not completed' % command[1].strip())

        if capi_elem[0] == 'sta_associate':
            time.sleep(10)


def send_capi_command(toaddr, capi_elem):
    """
    Send CAPI commands through socket based on IP address and
    port number

    Parameters
    ----------
    toaddr : str
        IP address and port number
    capi_elem : tuple of str
        CAPI command followed by parameters with "," as delimiter

    Returns
    -------
    status : str
        Contains string specifying command is running, complete
        or returning values

    Examples
    --------
    send_capi_command(192.168.0.1:9000, ca_get_version)
    send_capi_command(192.168.0.1:9000, sniffer_control_filter_capture,
        infile,_521-step1,outfile,521-step1_A,
        srcmac,00:11:22:33:44:55,destmac,55:44:33:22:11:00)
    """
    global iDNB, iINV, socktimeout, deftimeout
    capi_run = ','.join(capi_elem)          
    capi_cmd = capi_run + ' \r\n'
    asock = conntable.get(toaddr)
    for key in conntable.keys():
        if conntable[key] == asock:
            ipa = key.split(':')[0]
            ipp = key.split(':')[1]
    asock.send(capi_cmd)
    displayaddr = toaddr
    if toaddr in DisplayNameTable:
        displayaddr = DisplayNameTable[toaddr]
    logging.info("%s (%-15s) ---> %s" % (displayaddr, toaddr, capi_cmd.rstrip('\r\n')))
    if (capi_cmd.find("$") != -1): 
        set_color(FOREGROUND_RED | FOREGROUND_INTENSITY)
        logging.info("Test Case Criteria Failure - Found uninitialized variable ($)")
        set_color(FOREGROUND_INTENSITY)
    if socktimeout > 0 :
        asock.settimeout(socktimeout)
    else:
        asock.settimeout(deftimeout)

    try:
        #status = asock.recv(2048)
        status = read1line(asock)
        while not re.search(STATUS_CONST[0], status, re.I):
            logging.debug("\n          MSG: expect <status,RUNNING> but return - :%s:" % status)
            status = read1line(asock)
    except:
        exc_info = sys.exc_info()
        logging.error('Control Network Timeout - Connection Error, REASON = %s', exc_info[1])
        time.sleep(5)
        process_ipadd("ipaddr=%s,port=%s" % (ipa,ipp),1)
        asock = conntable.get(toaddr)
        asock.send(capi_cmd)
        logging.info("%s (%-15s) ---> %s" % (displayaddr, toaddr, capi_cmd.rstrip('\r\n')))

        asock.settimeout(deftimeout)            
        #status = asock.recv(2048)
        status = read1line(asock)
        while not re.search(STATUS_CONST[0], status, re.I):
            logging.debug("\nReceive error: expect <status,RUNNING> but return - %s" % status)
            status = read1line(asock)

        logging.debug( "%s (%s) <--- [%s]" % (displayaddr, toaddr, status.rstrip('\r\n' )))

    # Status,Running
    # Quick fix for case where AzWTG sends response RUNNING and COMPLETED in one read
    if (len(status) > 25):
        if re.search(STATUS_CONST[1], status, re.I) or re.search(STATUS_CONST[2], status, re.I) or re.search(STATUS_CONST[3], status, re.I):
            status = status.split('\n')
            status = status[1]
        elif status.find("status,RUNNING\r\n") != -1:
            status = status.replace('status,RUNNING\r\n', '')
        elif status.find("status,RUNNING\n\r") != -1:
            status = status.replace('status,RUNNING\n\r', '')
        elif status.find("status,RUNNING") != -1:
            logging.info("Missing new line after status,RUNNING")
            status = status.replace('status,RUNNING', '')
    else:
        if iDNB == 0:
            status = asock.recv(2048)
            #status = read1line(asock)
            if not (re.search(STATUS_CONST[1], status, re.I) or re.search(STATUS_CONST[2], status, re.I) or re.search(STATUS_CONST[3], status, re.I)):
                logging.debug("\nReceive error: expect <status,COMPLETE|INVALID|ERROR> but return - %s" % status)
                #status = read1line(asock)
        else:
            iDNB = 0

    if displayaddr == cSLog.name:
        cSLog.log("%s ---> %s" % (displayaddr, capi_cmd.rstrip('\r\n')))
        cSLog.log("%s <--- %s\n" % (displayaddr, status.rstrip('\r\n')))

    if re.search("FAIL", status) and re.search("SNIFFER", displayaddr) and iINV == 0:
        logging.info("%s <--- %s\n" % (displayaddr, status.rstrip('\r\n')))
        wfa_sys_exit ("Test Case Criteria Failure - Command returned FAIL")
    return status

def process_cmdfile(line):
    """
    Process the file line by line based on file name and path specified

    Parameters
    ----------
    line : str
        File name and path

    Returns
    -------
    none

    Example
    --------
	process_cmdfile(C:\\WTS_UCC_Windows\\cmds\\11n\\STA_5.2.1.txt)
    """
    i = 0
    line = line.rstrip()
    filelist = []
    filelist = line.split(',')
    nfile = len(filelist)
    while i < nfile:
        logging.debug('Command file ---' + filelist[i])
        file = open(filelist[i])
        scanner(file, process_cmd)
        file.close()
        i = i+1

def set_test_result(result, data, rdata):
    """Print TMS ending result to console"""
    global tmsPacket
    XLogger.setTestResult(result, data, rdata)
    if re.search("PASS", result):
        set_color(FOREGROUND_GREEN | FOREGROUND_INTENSITY)
        logging.info("\n     TEST RESULT ---> %15s" % result)
        tmsPacket.TestResult = "PASS"
        tmsPrint()
    elif re.search("FAIL", result):
        set_color(FOREGROUND_RED | FOREGROUND_INTENSITY)
        logging.info("\n     TEST RESULT ---> %15s | %s |" % (result, data))
        tmsPacket.TestResult = "FAIL"
        tmsPrint()

#global to save config flag
#num_of_pass_required == 0 -> test pass, if all checks are passed
#num_of_pass_required >= 1  -> test pass, if any value of check is passed
#value > 1  -> test pass, if any value of check is passed
num_of_pass_required = 0
total_checks = 0

def process_config_multi_subresults(line):
    global num_of_pass_required, total_checks
    try:
        cmd=line.split(',')

        if cmd[0] in  retValueTable:
            logging.debug("%s=%s" % (cmd[0],retValueTable[cmd[0]]))
        else:
            logging.info("Unknown variable %s" %cmd[0])
        if cmd[1] in  retValueTable:
            logging.debug("%s=%s" % (cmd[1],retValueTable[cmd[1]]))
        else:
            logging.info("Unknown variable %s" %cmd[1])

        logging.info("\n----------------Pass condition---------------------------\n")
        logging.info("Total number of checks = %s" % (retValueTable[cmd[1]]))
        logging.info("Number of pass required = %s" % (retValueTable[cmd[0]]))

        pass_required = int(retValueTable[cmd[0]])
        total_checks = int(retValueTable[cmd[1]])

        if pass_required == total_checks:
            #set true(1) to conditional_chk_flag in XLogger class
            XLogger.conditional_chk_flag = 1;
            num_of_pass_required = total_checks 
        elif pass_required < total_checks:
            #set true(1) to conditional_chk_flag in XLogger class
            XLogger.conditional_chk_flag = 1;
            num_of_pass_required = pass_required
        else:
            ## ignore if num of pass required > total num, and set default value 0
            num_of_pass_required = 0
            total_checks = 0
	
    except:
        exc_info = sys.exc_info( )
        set_color(FOREGROUND_RED | FOREGROUND_INTENSITY)
        logging.info("Test Case Criteria Failure - Invalid Pass/Fail Formula - %s" % exc_info[1])
        set_color(FOREGROUND_INTENSITY)
        logging.error('Test Case Criteria Failure - Invalid Pass/Fail Formula - %s' % exc_info[1])

def process_passFailWMM_2(line):
    """Determines pass or fail for WMM based on results and what is expected"""
    global runningPhase
    try:
        cmd = line.split(',')
        P1 = -1
        P2 = -1

        for p in streamRecvResultArray:
            if p.streamID == retValueTable[cmd[0]] and int(p.phase) == int(runningPhase):
                P1 = p.rxBytes
            elif p.streamID == retValueTable[cmd[1]] and int(p.phase) == int(runningPhase):
                P2 = p.rxBytes
        if cmd[2] in retValueTable:
            cmd[2] = retValueTable[cmd[2]]

        if (int(P2) <= 0) or (int(P1) <= 0):
            actual = -1
        else:
            actual = (float(P2) / float(P1)) * 100

        if actual >= long(cmd[2]):
            set_color(FOREGROUND_GREEN | FOREGROUND_INTENSITY)
            result = cmd[3]
        else:
            set_color(FOREGROUND_RED | FOREGROUND_INTENSITY)
            result = cmd[4]

        logging.info("\n       ----------------RESULT---------------------------\n")
        logging.info("Expected  >= %s %s" % (cmd[2], "%"))
        logging.info("Actual -  %6.6s %s" % (actual, "%"))
        logging.info("TEST RESULT ---> %s" % result)
        logging.info("\n       ------------------------------------------------")
        set_color(FOREGROUND_INTENSITY)
        set_test_result(result, "%6.6s %s" % (actual, "%"), ">= %s %s" % (cmd[2], "%"))
    except:
        exc_info = sys.exc_info()
        set_color(FOREGROUND_RED | FOREGROUND_INTENSITY)
        logging.info("Test Case Criteria Failure - Invalid Pass/Fail Formula - %s" % exc_info[1])
        set_color(FOREGROUND_INTENSITY)
        logging.error('Test Case Criteria Failure - Invalid Pass/Fail Formula - %s' % exc_info[1])   

def process_passFailWMM_1(line):
    """Determines pass or fail for WMM based on results and what is expected"""
    global runningPhase
    try:
        cmd = line.split(',')
        P1 = -1
        P2 = -1

        for p in streamRecvResultArray:
            if p.streamID == retValueTable[cmd[0]] and int(p.phase) == int(runningPhase):
                P1 = p.rxBytes
            elif p.streamID == retValueTable[cmd[1]] and int(p.phase) == int(runningPhase):
                P2 = p.rxBytes
        if cmd[2] in retValueTable:
            cmd[2] = retValueTable[cmd[2]]

        if (int(P2) <= 0) or (int(P1) <= 0):
            actual = -1
        else:
            actual = (float(P2) / float(P1)) * 100

        if actual <= long(cmd[2]):
            set_color(FOREGROUND_GREEN | FOREGROUND_INTENSITY)
            result = cmd[3]
        else:
            set_color(FOREGROUND_RED | FOREGROUND_INTENSITY)
            result = cmd[4]

        logging.info("\n       ----------------RESULT---------------------------\n")
        logging.info("Expected  <= %s %s" % (cmd[2], "%"))
        logging.info("Actual -  %6.6s %s" % (actual, "%"))
        logging.info("TEST RESULT ---> %s" % result)
        logging.info("\n       ------------------------------------------------")
        set_color(FOREGROUND_INTENSITY)
        set_test_result(result, "%6.6s %s" % (actual, "%"), "<= %s %s" % (cmd[2], "%"))
    except:
        exc_info = sys.exc_info()
        set_color(FOREGROUND_RED | FOREGROUND_INTENSITY)
        logging.info("Test Case Criteria Failure - Invalid Pass/Fail Formula - %s" % exc_info[1])
        set_color(FOREGROUND_INTENSITY)
        logging.error('Test Case Criteria Failure - Invalid Pass/Fail Formula - %s' % exc_info[1])   

def process_passFailWMM(line):
    """Determines pass or fail for WMM based on two phases result and what is expected"""
    try:
        cmd = line.split(',')
        P1 = -1
        P2 = -1

        if cmd[5] in retValueTable:
            cmd[5] = retValueTable[cmd[5]]

        for p in streamRecvResultArray:
            if p.streamID == retValueTable[cmd[0]] and int(p.phase) == 1:
                P1 = p.rxBytes
            elif p.streamID == retValueTable[cmd[1]] and int(p.phase) == 2:
                P2 = p.rxBytes

        if cmd[2] in retValueTable:
            cmd[2] = retValueTable[cmd[2]]

        if (int(P2) <= 0) or (int(P1) <= 0):
            actual = -1
        else:
            actual = (float(P2) / float(P1)) * 100

        if actual > long(cmd[2]):
            set_color(FOREGROUND_GREEN | FOREGROUND_INTENSITY)
            result = cmd[3]
        else:
            set_color(FOREGROUND_RED | FOREGROUND_INTENSITY)
            result = cmd[4]

        logging.info("\n       ----------------RESULT---------------------------\n")
        logging.info("%s Phase 1 = %s Bytes | %s Phase 2 = %s Bytes " %(cmd[5], P1, cmd[5], P2))
        logging.info("Expected  > %s %s" % (cmd[2], "%"))
        logging.info("Actual -  %6.6s %s" % (actual, "%"))
        logging.info("TEST RESULT ---> %s" % result)
        logging.info("\n       ------------------------------------------------")
        set_color(FOREGROUND_INTENSITY)
        set_test_result(result, "%6.6s %s" % (actual, "%"), "> %s %s" % (cmd[2], "%"))
    except:
        exc_info = sys.exc_info()
        set_color(FOREGROUND_RED | FOREGROUND_INTENSITY)
        logging.info("Test Case Criteria Failure - Invalid Pass/Fail Formula - %s" % exc_info[1])
        set_color(FOREGROUND_INTENSITY)
        logging.error('Test Case Criteria Failure - Invalid Pass/Fail Formula - %s' % exc_info[1])    

def process_passFailIBSS(line):
    """Determines pass or fail for IBSS based on results and what is expected"""
    try:
        cmd = line.split(',')
        P1 = -1
        logging.debug("Processing PASS/FAIL...")
        for p in streamRecvResultArray:
            if p.streamID == retValueTable[cmd[0]]:
                P1 = p.rxBytes
                break
        logging.info(" Received = %s Bytes Duration = %s Seconds Expected = %s Mbps " % (P1, cmd[2], cmd[1]))
        logging.debug(" B = %s B1 = %s" % (((long(P1) / 10000)), ((float(cmd[1]) * 125000))))
        if int(P1) <= 0:
            actual = -1
        else:
            actual = ((float(P1) * 8)) / (1000000 * int(cmd[2]))

        logging.info("Expected = %s Mbps  Received =%s Mbps" % (cmd[1], actual))
        if float(actual) >= float(cmd[1]):
            result = cmd[3]
        else:
            result = cmd[4]
        set_test_result(result, "-", "-")

    except:
        exc_info = sys.exc_info()
        set_color(FOREGROUND_RED | FOREGROUND_INTENSITY)
        logging.info("Test Case Criteria Failure - Invalid Pass/Fail Formula - %s" % exc_info[1])
        set_color(FOREGROUND_INTENSITY)
        logging.error('Test Case Criteria Failure - Invalid Pass/Fail Formula - %s' % exc_info[1])

def process_CheckThroughput(line, Trans):
    """Determines throughput and prints the results and expected to logs"""
    try:
        cmd = line.split(',')

        if cmd[2] in retValueTable:
            cmd[2] = retValueTable[cmd[2]]
        if cmd[3] in retValueTable:
            cmd[3] = retValueTable[cmd[3]]

        P1 = -1
        logging.debug("Processing Throughput Check...")
        if Trans:
            for p in streamSendResultArray:
                if p.streamID == retValueTable[cmd[0]] and int(p.phase) == int(cmd[1]):
                    P1 = p.rxBytes
                    break
        else:
            for p in streamRecvResultArray:
                if p.streamID == retValueTable[cmd[0]] and int(p.phase) == int(cmd[1]):
                    P1 = p.rxBytes
                    break

        if int(P1) <= 0:
            actual = -1
        else:
            actual = ((float(P1) * 8))/(1000000 * int(cmd[2]))

        if float(actual) >= float(cmd[3]):
            result = cmd[4]
        else:
            result = cmd[5]

        logging.debug(" Received = %s Bytes Duration = %s Seconds Expected = %s Mbps " % (P1, cmd[2], cmd[3]))
        logging.info("\n Expected >= %s Mbps Actual = %s Mbps" % (cmd[3], actual))
        set_test_result(result, "%s Mbps" %(actual), "%s Mbps" %(cmd[3]))

    except:
        exc_info = sys.exc_info()
        set_color(FOREGROUND_RED | FOREGROUND_INTENSITY)
        logging.info("Test Case Criteria Failure - Invalid Pass/Fail Formula - %s" % exc_info[1])
        set_color(FOREGROUND_INTENSITY)
        logging.error('Test Case Criteria Failure - Invalid Pass/Fail Formula - %s' % exc_info[1])

def process_CheckMCSThroughput(line):
    """Determines MCS throughput and prints the results and expected to logs"""
    try:
        cmd = line.split(',')
        logging.debug("process_CheckMCSThroughput")
        logging.debug("-%s-%s-%s-%s-%s" % (cmd[0], cmd[1], cmd[2], cmd[3], cmd[4]))

        TX = -1
        RX1 = -1
        RX2 = -1
        logging.debug("Processing Throughput Check...")
        for p in streamSendResultArray:
            if p.streamID == retValueTable[cmd[1]] and int(p.phase) == int(cmd[0]):
                TX = long(p.txBytes)
                break
        for p in streamRecvResultArray:
            if p.streamID == retValueTable[cmd[2]] and int(p.phase) == int(cmd[0]):
                RX1 = long(p.rxBytes)
            if p.streamID == retValueTable[cmd[3]] and int(p.phase) == int(cmd[0]):
                RX2 = long(p.rxBytes)

        logging.debug("-%s-%s-%s-%s" % (TX, RX1, RX2, cmd[4]))
        TX = (long(TX)* (float(cmd[4])/100))
        actual = -1
        if int(TX) <= 0:
            actual = -1
        else:
            if RX1 > TX and RX2 > TX:
                actual = 1

        if float(actual) > 0:
            result = cmd[5]
        else:
            result = cmd[6]

        logging.info("\n MCS Expected %s bytes, actual %s bytes and %s bytes" % (TX, RX1, RX2))
        set_test_result(result, "%s Bytes %s Bytes" %(RX1, RX2), "%s Bytes" % (TX))

    except:
        exc_info = sys.exc_info()
        set_color(FOREGROUND_RED | FOREGROUND_INTENSITY)
        logging.info("Test Case Criteria Failure - Invalid Pass/Fail Formula - %s" % exc_info[1])
        set_color(FOREGROUND_INTENSITY)
        logging.error('Test Case Criteria Failure - Invalid Pass/Fail Formula - %s' % exc_info[1])

def process_CheckDT4(line):
    """Determines amount of DT4 packets and prints the results and expected to logs"""
    try:
        cmd = line.split(',')
        logging.debug("process_Check DT4 Results")
        logging.debug("-%s-%s-%s-%s-%s-%s" % (cmd[0], cmd[1], retValueTable[cmd[1]], cmd[2], cmd[3], cmd[4]))
        RX = -1
        for p in streamSendResultArray:
            if p.streamID == retValueTable[cmd[1]] and int(p.phase) == int(cmd[0]):
                RX = long(p.rxFrames)

        logging.debug("-%s-%s" % (RX, cmd[2]))

        actual = -1
        if long(RX) > long(cmd[2]):
            actual = 1

        if float(actual) > 0:
            result = cmd[3]
        else:
            result = cmd[4]

        logging.info("\n DT4 Expected > %s packets, actual %s packets" % (cmd[2], RX))
        set_test_result(result, "%s Packets" %(RX), "%s Packets" % (cmd[2]))

    except:
        exc_info = sys.exc_info()
        set_color(FOREGROUND_RED | FOREGROUND_INTENSITY)
        logging.info("Test Case Criteria Failure - Invalid Pass/Fail Formula - %s" % exc_info[1])
        set_color(FOREGROUND_INTENSITY)
        logging.error('Test Case Criteria Failure - Invalid Pass/Fail Formula - %s' % exc_info[1])

def process_ResultCheck(line):
    """Determines pass or fail at the end of the test run"""
    try:
        cmd = line.split(',')
        logging.debug("%s-%s-%s-%s-%s-%s" % (retValueTable[cmd[0]], int(retValueTable["%s" % retValueTable[cmd[0]]]), cmd[0], cmd[1], cmd[2], cmd[3]))
        if int(retValueTable["%s" % retValueTable[cmd[0]]]) >= int(cmd[1]):
            result = cmd[2]
            XLogger.setTestResult(result)
        else:
            result = cmd[3]

            XLogger.setTestResult(result)
        logging.info("\nRESULT CHECK---> %15s" % result)
        XLogger.writeXML()

    except:
        exc_info = sys.exc_info()
        set_color(FOREGROUND_RED | FOREGROUND_INTENSITY)
        logging.info("Test Case Criteria Failure - Invalid Pass/Fail Formula - %s" % exc_info[1])
        set_color(FOREGROUND_INTENSITY)
        logging.error('Test Case Criteria Failure - Invalid Pass/Fail Formula - %s' % exc_info[1])

def get_reset_default_file():
    return retValueTable.setdefault('testfailreset', None)
def wfa_print_result(expt_flag, msg=""):
    """Print ending result to console"""
    global tmsPacket,num_of_pass_required,total_checks

    tmsPacket.TestResult = "FAIL"
    time.sleep(2)
    if expt_flag == 0 and XLogger.result == "NOT COMPLETED":
        set_color(FOREGROUND_RED | FOREGROUND_INTENSITY)
        XLogger.setTestResult("ABORTED")
        tmsPacket.TestResult = "FAIL"
        tmsPrint()

    elif expt_flag == 1:
        if XLogger.resultChangeCount >= 1:
            if XLogger.multiStepResultDict["FAIL"] > 0:
                if XLogger.conditional_chk_flag == 1:
                    if num_of_pass_required <= XLogger.pass_count:
                        set_color(FOREGROUND_GREEN | FOREGROUND_INTENSITY)
                        logging.info ("\n    FINAL TEST RESULT  ---> %15s" % "PASS")
                        tmsPacket.TestResult = "PASS"
                        tmsPrint()
                    else:
                        set_color(FOREGROUND_RED | FOREGROUND_INTENSITY)
                        logging.info ("\n    FINAL TEST RESULT ---> %15s" % "FAIL")
                        tmsPacket.TestResult = "FAIL"
                        tmsPrint()
                else :
                    set_color(FOREGROUND_RED | FOREGROUND_INTENSITY)
                    logging.info ("\n    FINAL TEST RESULT ---> %15s" % "FAIL")
                    tmsPacket.TestResult = "FAIL"
                    tmsPrint()
            else:
                set_color(FOREGROUND_GREEN | FOREGROUND_INTENSITY)
                logging.info("\n    FINAL TEST RESULT  ---> %15s" % "PASS")
                tmsPacket.TestResult = "PASS"
                tmsPrint()
        else:
            set_color(FOREGROUND_CYAN | FOREGROUND_INTENSITY)
            logging.info("TEST COMPLETED")
    else:
        set_color(FOREGROUND_CYAN | FOREGROUND_INTENSITY)
        if XLogger.result == "PASS" or XLogger.result == "FAIL":
            logging.info("------------")
            tmsPacket.TestResult = XLogger.result
            logging.info ("\n    FINAL TEST RESULT ---> %15s" % XLogger.result)
            tmsPrint()
            #PASS or FAIL status should not come into this logic, but if it does, it shouldn't print any error..
        else :
            XLogger.setTestResult("FAIL")
            logging.info ("\n    FINAL TEST RESULT ---> %15s" % "FAIL")
            tmsPacket.TestResult = "FAIL"
            tmsPrint()

    #JIRA SIG-1298
    num_of_pass_required = 0
    total_checks = 0
    XLogger.pass_count = 0
    XLogger.fail_count = 0
    XLogger.conditional_chk_flag = 0

    XLogger.writeXML()
####################################################################

def wfa_sys_exit(msg=""):
    """Exiting because an error has occurred or r_info get called to finish the test"""
    global errdisplayed

    #time.sleep(2)
    if re.search("r_info", msg):
        raise StandardError("%s" % msg)
    if re.search("Sniffer returned FAIL", msg):
        set_test_result("FAIL","-","Sniffer returned FAIL")
        XLogger.setTestResult("FAIL")
        XLogger.writeXML()
        raise StandardError()
    if re.search("ABORTED Response timeout", msg):
        set_test_result("FAIL","-","thread waiting time out")
        XLogger.setTestResult("FAIL")
        XLogger.writeXML()
        raise StandardError()
    if re.search("NO ASSOCIATION", msg):
        set_test_result("FAIL","-","NO ASSOCIATION")
        XLogger.setTestResult("FAIL")
        XLogger.writeXML()
        raise StandardError()
    set_color(FOREGROUND_RED | FOREGROUND_INTENSITY)
    if re.search("not applicable", msg) or re.search("not supported", msg):
        XLogger.setTestResult("TEST N/A")
    else:
        XLogger.setTestResult("ABORTED", msg)
        if (errdisplayed == 0):
            logging.info("ABORTED-: %s" % msg)
            errdisplayed=1
    if msg.find("10060") != -1:
        set_color(FOREGROUND_RED | FOREGROUND_INTENSITY)
        logging.info('Please check the following:')
        logging.info('	- Make sure destination IP Address is set correctly')
        logging.info('	- Make sure remote device has firewall turned off')
        logging.info('	- Make sure control network cable is connected')
        set_color(FOREGROUND_INTENSITY)
    elif msg.find("10061") != -1:
        set_color(FOREGROUND_RED | FOREGROUND_INTENSITY)
        logging.info('Connection Could Be Refused - Please check the following:')
        logging.info('	- Make sure WTS CA is started')
        logging.info('	- Make sure destination port number is set correctly')
        set_color(FOREGROUND_INTENSITY)

    XLogger.writeXML()
    raise StandardError("%s" % msg)

def wfa_sys_exit_0():
    """Exiting because r_info command got called"""
    global tmsPacket
    time.sleep(2)
    set_color(FOREGROUND_BLUE | FOREGROUND_INTENSITY)
    XLogger.writeXML()
    tmsPacket.TestResult = "PASS"
    raise StandardError("END-0-r_info")

class XMLLogHandler(logging.FileHandler):

    def emit(self, record):
        try:
            XLogger.log(self.format(record))
            self.flush()
        except:
            self.handleError(record)

XLogger = ""

def init_logging(_filename, level, loop=0):
    global cSLog, XLogger, tmsPacket, tmsLogLocation, tmsTimeStamp
    p = _filename.split('\\')
    resultCollectionFile = open("TestResults", "a")
    for s in p:
        tFileName = s

    tmsTimeStamp = time.strftime("%b-%d-%Y__%H-%M-%S", time.localtime())
    directory= "./log/%s_%s" %(tFileName.rstrip(".txt"),tmsTimeStamp)
    tmsLogLocation = directory

    os.mkdir(directory)
    retValueTable["$logDir"] = directory.lstrip("./log")

    os.system("echo %s > p" % directory)

    fname = "%s/log_%s.log" %(directory, tFileName.rstrip(".txt"))
    fname_sniffer = "%s/sniffer_log_%s.log" % (directory, tFileName.rstrip(".txt"))

    logStream = open(fname, "w")

    tmsPacket.TestCaseId = tFileName.rstrip(".txt")
    tmsPacket.LogFileName = fname

    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s %(levelname)-8s %(message)s',
                        datefmt='%a, %d %b %Y %H:%M:%S',
                        stream=logStream)

    if not loop:
        cSLog = classifiedLogs("SNIFFER", fname_sniffer, "SNIFFER CHECKS LOG - Testcase: %s \n\n" % tFileName.rstrip(".txt"))

        #a Handler which writes INFO messages or higher to the sys.stderr

        console = logging.StreamHandler()

        if level == '2':
            console.setLevel(logging.DEBUG)
        else:
            console.setLevel(logging.INFO)
        # set a format which is simpler for console use
        formatter = logging.Formatter('%(levelname)-8s %(message)s')
        # tell the handler to use this format
        console.setFormatter(formatter)
        # add the handler to the root logger
        if level != '0':
            logging.getLogger('').addHandler(console)
        set_color(FOREGROUND_INTENSITY)
    else:
    # replace the stream
        for each in logging.getLogger('').handlers:
            if re.search("log_", "%s" % each.stream):
                each.stream.close()
                each.stream = logStream

    # Add XML Log Handler
    XLogger = XMLLogger("%s/%s_%s.xml" %
                        (directory,
                         tFileName.rstrip(".txt"),
                         time.strftime("%Y-%m-%dT%H_%M_%SZ",
                         time.localtime())),
                         "%s" % (tFileName.rstrip(".txt")))
    hXML = XMLLogHandler('t')
    XMLformatter = logging.Formatter('%(message)s')
    hXML.setFormatter(XMLformatter)
    if not loop:
        logging.getLogger('').addHandler(hXML)

    tmsPacket.getTestID(VERSION)

    logging.info("###########################################################\n")
    logging.info("UCC Version [%s]" % VERSION)
    logging.info('Logging started in file - %s' % (fname))

def reset():
    """Resets all global variables"""
    global retValueTable, DisplayNameTable, streamSendResultArray, streamRecvResultArray, streamInfoArray, streamInfoArrayTemp, lhs, rhs, oper, boolOp, runningPhase, testRunning, threadCount, resultPrinted, ifcondBit, ifCondBit, iDNB, iINV, RTPCount
    logging.debug("Reset After Test End")

    retValueTable = {}
    DisplayNameTable = {}
    streamSendResultArray = []
    streamRecvResultArray = []
    streamInfoArray = []
    streamInfoArrayTemp = []
    lhs = []
    rhs = []
    oper = []
    boolOp = []
    runningPhase = '1'
    testRunning = 0
    threadCount = 0
    resultPrinted = 0
    ifcondBit = 1
    ifCondBit = 1
    iDNB = 0
    iINV = 0
    RTPCount = 1
    set_color(FOREGROUND_WHITE)

def firstword(line):
    global maxThroughput, payloadValue, uccPath
    str = line.split('#')
    command = str[0].split('!')

    if command[0] == 'wfa_control_agent' or command[0] == 'wfa_control_agent_dut':
        if retValueTable["$WTS_ControlAgent_Support"] != "0":
            process_ipadd(command[1])
            retValueTable.setdefault(command[0], "%s:%s" % ((command[1].split(',')[0]).split('=')[1], (command[1].split(',')[1]).split('=')[1]))
        else:
            if ("$WTS_TrafficAgent_Support" in retValueTable):
                if (retValueTable["$WTS_TrafficAgent_Support"] == "1"):
                    process_ipadd(command[1])
                    retValueTable.setdefault(command[0], "%s:%s" % ((command[1].split(',')[0]).split('=')[1], (command[1].split(',')[1]).split('=')[1]))

    elif  command[0] == 'wfa_console_ctrl' or command[0] == 'wfa_wfaemt_control_agent' or command[0] == 'wfa_adept_control_agent' or re.search('control_agent_testbed_sta', command[0]) or re.search('control_agent', command[0]) or re.search('TestbedAPConfigServer', command[0]) or re.search('wfa_sniffer', command[0]) or re.search('ethernet', command[0]):
        process_ipadd(command[1])
        retValueTable.setdefault(command[0], "%s:%s" % ((command[1].split(',')[0]).split('=')[1], (command[1].split(',')[1]).split('=')[1]))
    elif command[0].lower() == 'exit':
        wfa_sys_exit("CAPI exit command - %s" % command[1])
    elif command[0].lower() == 'info':
        if command[1] in retValueTable:
            command[1] = retValueTable[command[1]]
        logging.info("\n %7s ~~~~~ %s ~~~~~ \n" %("", command[1]))
    elif command[0] == 'wfa_test_commands':
        logging.debug('Processing wfa_test_commands')
        process_cmdfile("%s%s" % (uccPath, command[1]))
    elif command[0] == 'wfa_test_commands_init':
        logging.debug('Processing init wfa_test_commands')
        logging.debug("UCC Path = %s" % uccPath)
        s1 = command[1]
        scanner(open(uccPath + s1), firstword)
    elif re.search('testfailreset',command[0]):
        if len(command) >= 2:
            retValueTable[command[0]] = command[1]
    if "$TestNA" in retValueTable:
        logging.error("%s" % retValueTable["%s" % "$TestNA"])
        wfa_sys_exit("%s" % retValueTable["%s" % "$TestNA"])
    elif command[0] == 'dut_wireless_ip' or command[0] == 'dut_default_gateway' or command[0] == 'wfa_console_tg' or re.search('wireless_ip', command[0]) or re.search('wmmps_console', command[0]) or re.search('tg_wireless', command[0]):
        retValueTable.setdefault(command[0], command[1])
    elif re.search('define', command[0]):
        if command[2] in retValueTable:
            command[2] = retValueTable[command[2]]
        if command[1] in retValueTable:
            retValueTable[command[1]] = command[2]
        else:
            retValueTable.setdefault(command[1], command[2])
    elif re.search('DisplayName', command[0]):
        if command[1] in retValueTable:
            DisplayNameTable.setdefault(retValueTable[command[1]], command[2])
        else:
            DisplayNameTable.setdefault(command[1], command[2])
    elif re.search('throughput', command[0]):
        maxThroughput = command[1]
        logging.info("Maximum Throughput %s Mbps" % maxThroughput)
        retValueTable.setdefault(command[0], command[1])
    elif re.search('payload', command[0]):
        payloadValue = command[1]
        logging.info("Payload =  %s Bytes", (command[1]))
        retValueTable.setdefault(command[0], command[1])
    elif re.search('stream', command[0]):
        logging.debug("STREAM = %s, Payload = %s Bytes, Percentage = %s %s of Maximum Throughput" %(command[0], payloadValue, command[1], "%"))
        frameRate = int(maxThroughput) * int(command[1])*1250/int(payloadValue)
        logging.info("%s %s Frames / second"  % (command[0], frameRate ))
        retValueTable.setdefault(command[0], "%s" % frameRate)
    if len(command) == 2:
        logging.debug("Command = %s" % (command[1]))

def tmsPrint():
    """function to run writeTMSJson()"""
    global tmsPacket,tmsLogLocation, tmsTimeStamp
    try :
        tmsPacket.writeTMSJson(tmsLogLocation, tmsTimeStamp)
    except :
        #exception
        logging.debug("TMS N/A")

def get_display_name(toaddr):
    displayName = toaddr
    if toaddr in DisplayNameTable:
        displayName= DisplayNameTable[toaddr]
    return displayName
    
