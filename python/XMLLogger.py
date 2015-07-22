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
import logging
import logging.handlers
import time
import xml.dom.minidom
from xml.dom.minidom import Document
from xml.dom.minidom import getDOMImplementation
from xml.dom.minidom import parse
from ResultSummary import TBDevice
from ResultSummary import WTSComponent

# Override createElement:
class XMLDoc(Document):
    def createElement(self, tag, textNode=None):
        el = Document.createElement(self, "%s" % tag)
        el.doc = self
        if textNode:
            el.appendChild(self.createTextNode(textNode))
        return el

class XMLLogger:
    def __init__(self, fileName, testID, stylesheet="..\\Log-Format.xsl"):
        self.fileName = fileName
        self.doc = XMLDoc()
        self.result = "NOT COMPLETED"
        #JIRA SIG-868
        self.resultChangeCount = 0
        self.multiStepResultDict = {"PASS" : 0, "FAIL" : 0}
        # Stylesheet
        self.doc.appendChild(self.doc.createProcessingInstruction("xml-stylesheet",
                             "type=\"text/xsl\" href=\"%s\"" % stylesheet))

        self.LogItemCounter = 1
        self.resultLogged = 0

        # Log
        self.Log = self.doc.createElement("Log")
        self.Log.setAttribute("id", testID)
        self.Log.setAttribute("time", "%s" % time.strftime("%Y-%m-%dT%H:%M:%SZ", time.localtime()))
        self.Log.setAttribute("uid", "1")
        self.doc.appendChild(self.Log)
        self.resultNode = self.doc.createElement("TestCaseResult")
        self.Log.appendChild(self.resultNode)

        # Info
        self.Info = self.doc.createElement("Info")
        self.Testbed = self.doc.createElement("Testbed")
        self.WTS = self.doc.createElement("WTS")
        self.DUT = self.doc.createElement("DUT")

        self.Log.appendChild(self.Info)
        self.Info.appendChild(self.Testbed)
        self.Info.appendChild(self.WTS)
        self.Info.appendChild(self.DUT)

        # Media Log
        self.mediaLogCounter = 0

    def setTestID(self, testID):
        self.Log.setAttribute("id", testID)

    def setTestResult(self, result, r1="", r2=""):
        self.result = result
        #JIRA SIG-868
        self.resultChangeCount += 1
        if "FAIL" in result:
            self.multiStepResultDict["FAIL"] += 1
        else:
            self.multiStepResultDict["PASS"] += 1
        #print("*----> Setting results [%s] [%s] [%s] [%s]" % (result, self.LogItemCounter,r1,r2))

    def setManualCheckInfo(self, mChk):
        self.Log.appendChild(self.doc.createElement("ManualCheckInfo", mChk))

    def addMediaLog(self, filename):
        if self.mediaLogCounter == 0:
            self.mediaLogNode = self.doc.createElement("MediaLog")
            self.Log.appendChild(self.mediaLogNode)

        self.mediaLogNode.appendChild(self.doc.createElement("MediaFile", filename))
        self.mediaLogCounter = self.mediaLogCounter + 1

        #print("*----> Setting results [%s] [%s] [%s] [%s]" % (result, self.LogItemCounter,r1,r2))

    def log(self, command):
        destName = ""
        destAddress = ""
        sourceName = ""
        sourceAddress = ""

        try:
            # Command UCC to TB
            if "-->" in command:
                c = command.split("-->")
                if len(c) > 1:
                    sourceName = "UCC"
                    command = c[1]
                    c1 = c[0].split('(')
                    if len(c1) > 0:
                        destName = c1[0]
                        destAddress = c1[1]
            # Command TB to UCC
            if "<--" in command:
                c = command.split("<--")
                if len(c) > 1:
                    destName = "UCC"
                    command = c[1]
                    c1 = c[0].split('(')
                    if len(c1) > 0:
                        sourceName = c1[0]
                        sourceAddress = c1[1]

        except:
            # Drop blank or unidentified format lines
            #print ("drop %s " % command)
            pass

        # Log Item
        LogItem = self.doc.createElement("LogItem")
        LogItem.setAttribute("id", "%s" % self.LogItemCounter)
        LogItem.setAttribute("type", "command")
        self.Log.appendChild(LogItem)

        # LogDetailLevel
        LogItem.appendChild(self.doc.createElement("LogDetailLevel", "Info"))

        # Date Time
        LogItem.appendChild(self.doc.createElement("DateTime", "%s" % time.strftime("%Y-%m-%dT%H:%M:%SZ", time.localtime())))

        # Command Group
        CGroup = self.doc.createElement("CommandGroup")
        LogItem.appendChild(CGroup)

        CGroup.appendChild(self.doc.createElement("Command", command))

        Dest = self.doc.createElement("Destination")
        CGroup.appendChild(Dest)
        Source = self.doc.createElement("Source")
        CGroup.appendChild(Source)

        Dest.appendChild(self.doc.createElement("Name", destName))
        Dest.appendChild(self.doc.createElement("Address", destAddress))
        Source.appendChild(self.doc.createElement("Name", sourceName))
        Source.appendChild(self.doc.createElement("Address", sourceAddress))

        self.LogItemCounter = self.LogItemCounter + 1

    def AddTestbedDevice(self, WTSControlAgent, vendor, model, driver, os=""):
        device = TBDevice(vendor, model, driver, os, WTSControlAgent)
        device.AddXMLNode(self.doc, self.Testbed)
        return

    def AddDUTInfo(self, WTSControlAgent, vendor, model, driver, os=""):
        device = TBDevice(vendor, model, driver, os, WTSControlAgent)
        device.AddXMLNode(self.doc, self.DUT)
        return

    def AddWTSComponent(self, name, version, others):
        comp = WTSComponent()
        comp.name = name
        comp.version = version
        comp.others = others
        comp.AddXMLNode(self.doc, self.WTS)
        return

    def writeXML(self):
        if not self.resultLogged:
            # Test case result
            self.resultNode.appendChild(self.doc.createTextNode(self.result))
            fXMLFile = open(self.fileName, "w")
            fXMLFile.write(self.doc.toprettyxml(indent=" "))
            fXMLFile.close()
            self.resultLogged = 1
        return

    def __str__(self):
        pass



XLogger = XMLLogger("log\\abc.xml", "P2P-5.1.12", "..\\Log-Format.xsl")

class abc(logging.FileHandler):
    def emit(self, record):
        try:
            XLogger.log(self.format(record))
            self.flush()
        except:
            self.handleError(record)

def init_logging(_filename):
    logging.basicConfig(level=logging.INFO,
                        format='%(message)s',
                        datefmt='%a, %d %b %Y %H:%M:%S',
                        filename=_filename,
                        filemode='w')
    console = logging.StreamHandler()
    m = abc('tmp')

    console.setLevel(logging.DEBUG)

    formatter = logging.Formatter('%(message)s')
    mformatter = logging.Formatter('%(message)s')
    console.setFormatter(formatter)
    m.setFormatter(mformatter)
    # add the handler to the root logger
    logging.getLogger('').addHandler(console)
    logging.getLogger('').addHandler(m)

    logging.info("###########################################################\n")
    logging.info('Logging started in file - %s' % (_filename))

# only for unit testing. main() function should be removed during integration with UCC core
def main():
    global XLogger
    #rSummary = ResultSummary("log\\summary.xml","1","log")
    init_logging("test.txt")
    #rLog = open("sample.txt","r")
    logPath = "\\\\Input\\Your\\Log\\Location"

    for f in os.listdir(logPath):
        print f
        if f.startswith("P2P"):
            for f1 in os.listdir(logPath + "\\" + f):
                print f1
                XLogger.fileName = "log\\%s.xml" % f
                XLogger.setTestID("%s"%f.split("_")[0])
                XLogger.AddTestbedDevice("xx.xx.xx", "CompanyB", "ABCDEF-123456", "5", "Linux")
                XLogger.AddTestbedDevice("WINvxx.xx.xx", "CompanyA", "123ABCD", "xx.x.xxx.xx", "Win7")
                XLogger.AddWTSComponent("UCC", "4.1.0", "09022010_1")
                XLogger.AddWTSComponent("Sniffer", "4.1.0", "Wireshark 1.4.0-rc1")
                logging.info("---- Opening File [%s]" % logPath + "\\" + f + "\\"+ f1)

                rLog = open(logPath + "\\" + f + "\\"+ f1, "r")
                for r in rLog:
                    r1 = r.split('INFO')
                    if len(r1) > 1:
                        logging.info(r1[1])
                    else:
                        logging.info(r1[0])
                XLogger.writeXML()
                XLogger = XMLLogger("log\\abc.xml", "P2P-5.1.12", "..\\Log-Format.xsl")

    #XLogger.writeXML()
    #rSummary.writeXML()

if __name__ == "__main__":
    main()
