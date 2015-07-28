#!/usr/bin/env python

import os
import sys
import glob
import re
try:
	import xml.etree.cElementTree as ET
except ImportError:
	import xml.etree.ElementTree as ET

tree = ET.parse('UCCSyntax.xml')
root = tree.getroot()

pythonPath = os.path.dirname(os.path.abspath(__file__))
UCCpath = os.path.dirname(os.path.dirname(pythonPath))
cmdspath = os.path.join(UCCpath, 'cmds') 

totalSyntaxErrors = 0

#These files have special formatting that should generally be ignored by the syntax checker
fileSkipList = {"WTS-11n": ["InitEnv.txt", "TestbedAPNames.txt"], 
				"WTS-P2P": ["InitEnv.txt", "discoverability-req.txt", "discoverability-req-frame.txt", "ucc-probe-req.txt"],
				"WTS-VHT": ["InitEnv.txt", "TestbedAPNames.txt", "Review Cases.txt"],
				"WTS-WFD": ["InitEnv.txt", "MappingTable_VESA.txt", "MappingTable_CEA.txt", "BaseMappingTable.txt", "MappingTable_HH.txt", "DUT-WFD-Check-Optional.txt"],
				"WTS-WFDS": ["InitEnv.txt", "Init_Definitions.txt"],
				"WTS-PMF": ["InitEnv.txt", "TestbedAPNames.txt"],
				"WTS-HS2": ["InitEnv.txt", "Default-Param.txt", "TestbedAPNames.txt", "Manual-APUT.txt", "4.3_step2.txt", "4.3_step4.txt", "4.3_step6.txt", "4.3_step8.txt", "4.3_step10.txt", "4.3_step12.txt", "4.3_step14.txt", "arp_neigh_loop", "5.3_arp_request.txt", "5.3_arp_reply.txt"],
				"WTS-HS2-R2": ["InitEnv.txt", "Default-Param.txt", "TestbedAPNames.txt", "RADIUS-Servers_Details.txt", "Manual-APUT.txt", "Certificate_Details.txt", "URLs_OSU_Mapping.txt", "PPSMO_Details.txt", "PPSMO_Details-Aruba.txt", "UserName_Details-Aruba.txt", "UserName_Details-Ruckus.txt", "PPSMO_Details-Ruckus.txt", "Icon_Details.txt", "Friendly_Names_Icons.txt", "Configure_SerialNo.txt", 
								 "4.3_step2.txt", "4.3_step4.txt", "4.3_step6.txt", "4.3_step8.txt", "4.3_step10.txt", "4.3_step12.txt", "4.3_step14.txt", "5.3_arp_request.txt", "5.3_arp_reply.txt"],
				"WTS-WMMPS": ["InitEnv.txt", "TestbedAPNames.txt"],
				"WTS-NAN": ["InitEnv.txt", "init_scenario.txt", "FurtherAvail_reset.txt"]}

#These words have 0 or 1 exclamation marks as delimiters and should generally be ignored by the syntax checker
wordSkipList = ["else", "endif", "_inv", "inv_", "pause", "info", "GetUCCSystemTime", "exit", "_DNB_", "IfNoWTS"]

#hostMachine!commandName(keyValPairs)!returnVal
def isNormalCAPICommand(string):
	CAPI = string[1].split(',')
	retval = string[2]
	if ((len(CAPI) % 2) == 0):
		return False
	if (retval == "DEFAULT"):
		return True
	retval = retval.split(',')
	if (not (len(retval) == 2)):
		return False
	if (retval[1] == "dut_wireless_ipv6"): #Special exception for "dut_wireless_ipv6"; OK to not have '$'
		return True
	if (not (retval[1][0] == '$')):
		return False
	return True

#hostMachine!(keyValPairs)!returnVal
def isSpecialCAPICommand(string):
	CAPI = string[1].split(',')
	retval = string[2]
	if ((len(CAPI) % 2 == 0) and (retval == "DEFAULT")):
		return True
	return False

#hostMachine!commandName(keyValPairs)!ID,$,$
def isDoubleReturnCAPICommand(string):
	CAPI = string[1].split(',')
	retval = string[2].split(',')
	if ((len(CAPI) % 2) == 0):
		return False
	if (not (len(retval) == 3)):
		return False
	if (not ((retval[1][0] == '$') or (retval[2][0] == '$'))):
		return False
	return True

#hostMachine!commandName(keyValPairs)!returnVals
def isMultipleReturnCAPICommand(string):
	CAPI = string[1].split(',')
	retval = string[2].split(',')
	if ((len(CAPI) % 2) == 0):
		return False
	if (len(retval) > 2):
		return True

def isMACAddr(string):
	hexdigits = '0123456789abcdefABCDEF'
	if (not (re.match(r'(..):(..):(..):(..):(..):(..)', string))):
		return False
	string = string.split(':')
	for num in string:
		for char in num:
			if (char not in hexdigits):
				return False
	return True

def isIPv6Addr(string):
	hexdigits = '0123456789abcdefABCDEF'
	if (not (re.match(r'(.+):(.+):(.+):(.+):(.+):(.+):(.+):(.+)', string))):
		return False
	string = string.split(':')
	for num in string:
		for char in num:
			if (char not in hexdigits):
				return False
	return True

def isIPv4Addr(string):
	if (not (re.match(r'(\d+)\.(\d+)\.(\d+)\.(\d+)', string))):
		return False
	string = string.split('.')
	for num in string:
		if (not (num.isdigit())):
			return False
			if ((int(num) < 0) or (int(num) > 255)):
				return False
	return True

def isPortNumber(string):
	if (string.isdigit()):
		if ((int(string) >= 0) and (int(string) <= 65535)):
			return True
	return False

def isIPv4AddrAndPort(string):
	string = string.split(',')
	if (not (len(string) == 2)):
		return False
	ipaddr = string[0].split('=')
	port = string[1].split('=')
	if (not isIPv4Addr(ipaddr[1])):
		return False
	if (not isPortNumber(port[1])):
		return False
	return True

def isIPv4AddrSpacePort(string):
	string = string.split(' ')
	if (not (len(string) == 2)):
		return False
	ipaddr = string[0]
	port = string[1]
	if (not isIPv4Addr(ipaddr)):
		return False
	if (not isPortNumber(port)):
		return False
	return True

def checkLine(line, lineNumber, errorLog, name):
	global totalSyntaxErrors
	if (re.search(r' $', line)): 
		line = line.strip(' ') #get rid of whitespace at the end of lines for correct parsing
	orginalLine = line
	Cmd = []

	#XML tags can't start with a number, so append a '_' to lines that start with a number to match XML file
	if (line[0].isdigit()):
		line = 'DIGIT_' + line

	#Can't have AKA' be a tag in XML due to "'", so we need to change to AKA
	if (line [:12] == "define!$AKA'"):
		line = "define!$AKA" + line[12:]
	if (line[:4] == "AKA'"):
		line = "AKA" + line[4:]
	
	#Check for correct define syntax; will check key,value pairing later
	if (line[:6] == "define"): 
		if (not (line[6] == '!')):
			errorLog.append("Syntax error on line %d: expected '!' after \"define\"" % (lineNumber))
			totalSyntaxErrors += 1
			return True
		if (not (re.search(r'!$', line))):
			errorLog.append("Syntax error on line %d: expected '!' at the end of define statement" % (lineNumber))
			totalSyntaxErrors += 1
			return True
		#Placeholder error; add a dummy space character for correct parsing if third field of 'define' macro was left blank
		if (re.search(r'!!$', line)):
			line = line[:(len(line)-1)] + "FILL!"

	#Split into substrings based on the '!' delimeter
	line = line.split('!')
	for string in line:
		if (string != ''): #left over from removing \r
			Cmd.append(string)

	#Most likely a typo; check wordList for common commands in the form of "xxxx!"
	if (len(Cmd) == 1):
		if (Cmd[0] in wordSkipList):
			return False
		errorLog.append("Syntax error on line %d: %s is not a valid command" % (lineNumber, Cmd[0]))
		totalSyntaxErrors += 1
		return True
	#Command is in form "xxxx!xxxx!"; root[0] = DUTInfo Macros; root[1] = Init Macros
	elif (len(Cmd) == 2):
		#Check that the command ends in a '!'
		if (not re.search(r'!$', orginalLine)):
			errorLog.append("Syntax error on line %d: %s should end with a '!' symbol" % (lineNumber, orginalLine))
			totalSyntaxErrors += 1
			return True
		for element in root.iter():
			if (element.find(Cmd[0])):
				key = element.find(Cmd[0])
				for value in key:
					#re.match(r'(\d*)(\.?)(\d+)'
					if ((value.text == Cmd[1]) or (value.text == "ANYTHING") or (value.text == "FILL")):
						#We matched a key to a value
						return False #error found = false
					elif (value.text == "VARIABLE"):
						if (re.match(r'\$(.+)', Cmd[1])):
							return False
						else:
							errorLog.append("Syntax error on line %d: %s should begin with a '$' symbol" % (lineNumber, Cmd[1]))
							totalSyntaxErrors += 1
							return True
					elif (value.text == "INTEGER"):
						if (Cmd[1].isdigit()):
							return False
						else:
							errorLog.append("Syntax error on line %d: %s is not a valid integer" % (lineNumber, Cmd[1]))
							totalSyntaxErrors += 1
							return True
					elif (value.text == "FLOAT"):
						if (re.match(r'(\d*)(\.?)(\d+)', Cmd[1])):
							return False
						else:
							errorLog.append("Syntax error on line %d: %s is not a valid float" % (lineNumber, Cmd[1]))
							totalSyntaxErrors += 1
							return True
					elif (value.text == "IPv4ADDR"):
						if (isIPv4Addr(Cmd[1])):
							return False
						else:
							errorLog.append("Syntax error on line %d: %s is not a valid IPv4 address" % (lineNumber, Cmd[1]))
							totalSyntaxErrors += 1
							return True
					elif (value.text == "PORT"):
						if (isPortNumber(Cmd[1])):
							return False
						else:
							errorLog.append("Syntax error on line %d: %s is not a valid port number" % (lineNumber, Cmd[1]))
							totalSyntaxErrors += 1
							return True
					elif (value.text == "IPv4ADDR,PORT"):
						if (isIPv4AddrAndPort(Cmd[1])):
							return False
						else:
							if (len(Cmd[1].split(',')) > 2):
								errorLog.append("Syntax error on line %d: %s is not a valid CAPI Command" % (lineNumber, orginalLine))
								totalSyntaxErrors += 1
								return True
							else:
								errorLog.append("Syntax error on line %d: %s is not a valid IPv4, PORT combination" % (lineNumber, Cmd[1]))
								totalSyntaxErrors += 1
								return True
					elif (value.text == "TEXTFILE"):
						if (re.search(r'\.txt$', Cmd[1])):
							return False
						else:
							errorLog.append("Syntax error on line %d: %s is not a valid text file or variable" % (lineNumber, Cmd[1]))
							totalSyntaxErrors += 1
							return True
					elif (value.text == "IPv6ADDR"):
						if (isIPv6Addr(Cmd[1])):
							return False
						else:
							errorLog.append("Syntax error on line %d: %s is not a valid IPv6 address" % (lineNumber, Cmd[1]))
							totalSyntaxErrors += 1
							return True
					elif (value.text == "MEDIAFILE"):
						if (re.search(r'\.jpeg$', Cmd[1]) or re.search(r'\.mp4$', Cmd[1])):
							return False
						else:
							errorLog.append("Syntax error on line %d: %s is not a valid media file or variable" % (lineNumber, Cmd[1]))
							totalSyntaxErrors += 1
							return True
				errorLog.append("Syntax error on line %d: %s is not a valid value" % (lineNumber, Cmd[1]))
				totalSyntaxErrors += 1
				return True
		errorLog.append("Syntax error on line %d: %s is not a valid command" % (lineNumber, orginalLine))
		totalSyntaxErrors += 1
		return True
	#Check if define macro in the form define!xxxx!xxxx!; root[4] = Define Macros
	elif (len(Cmd) > 2):
		if (Cmd[0] == "define"):
			#Check if second parameter begins with a '$'
			#If so, no need to check syntax since variable isn't user-modified
			if (Cmd[2][0] == '$'):
				return False
			#XML does not support '$' in tags, so replace with "DOLLARSIGN_"
			#XML does not suppoer '.' in tags, so replace with "_DOT_"
			if (Cmd[1][0] == '$'):
				Cmd[1] = "DOLLARSIGN_" + Cmd[1][1:]
			Cmd[1] = Cmd[1].replace('.', "_DOT_")
			for element in root[4].iter():
				if element.find(Cmd[1]):
					key = element.find(Cmd[1])
					for value in key:
						if (value.text == Cmd[2] or (value.text == "ANYTHING") or (value.text == "FILL")):
							return False
						elif (value.text == "INTEGER"):
							if (Cmd[2].isdigit()):
								return False
							else:
								errorLog.append("Syntax error on line %d: %s is not a valid integer" % (lineNumber, Cmd[2]))
								totalSyntaxErrors += 1
								return True
						elif (value.text == "FLOAT"):
							if (re.match(r'(\d*)(\.?)(\d+)', Cmd[2])):
								return False
							else:
								errorLog.append("Syntax error on line %d: %s is not a valid float" % (lineNumber, Cmd[2]))
								totalSyntaxErrors += 1
								return True
						elif (value.text == "PORT"):
							if (isPortNumber(Cmd[2])):
								return False
							else:
								errorLog.append("Syntax error on line %d: %s is not a valid port number" % (lineNumber, Cmd[2]))
								totalSyntaxErrors += 1
								return True
						elif (value.text == "MACADDR"):
							if (isMACAddr(Cmd[2])):
								return False
							else:
								errorLog.append("Syntax error on line %d: %s is not a valid MAC address" % (lineNumber, Cmd[2]))
								totalSyntaxErrors += 1
								return True
						elif (value.text == "IPv4ADDR"):
							if (isIPv4Addr(Cmd[2])):
								return False
							else:
								errorLog.append("Syntax error on line %d: %s is not a valid IPv4 address" % (lineNumber, Cmd[2]))
								totalSyntaxErrors += 1
								return True
						elif (value.text == "IPv4ADDR PORT"):
							if (isIPv4AddrSpacePort(Cmd[2])):
								return False
							else:
								errorLog.append("Syntax error on line %d: %s is not a valid IPv4 PORT combination" % (lineNumber, Cmd[2]))
								totalSyntaxErrors += 1
								return True
						elif (value.text == "IPv6ADDR"):
							if (isIPv6Addr(Cmd[2])):
								return False
							else:
								errorLog.append("Syntax error on line %d: %s is not a valid IPv6 address" % (lineNumber, Cmd[2]))
								totalSyntaxErrors += 1
								return True
						elif (value.text == "TEXTFILE"):
							if (re.search(r'\.txt$', Cmd[2])):
								return False #error found = false
							else:
								errorLog.append("Syntax error on line %d: %s is not a valid text file or variable" % (lineNumber, Cmd[1]))
								totalSyntaxErrors += 1
								return True
					errorLog.append("Syntax error on line %d: %s is not a valid value" % (lineNumber, Cmd[2]))
					totalSyntaxErrors += 1
					return True
			#Revert back special characters for printing
			Cmd[1] = Cmd[1].replace("_DOT_", '.')
			Cmd[1] = Cmd[1].replace("DOLLARSIGN_", '$')
			errorLog.append("Syntax error on line %d: %s is not a valid command" % (lineNumber, orginalLine))
			totalSyntaxErrors += 1
			return True
		else:
			if (Cmd[0] == "TestbedAPConfigServer" or re.search(r'_ap$', Cmd[0])):
				if (re.search(r'^AccessPoint', Cmd[1]) or re.search(r'^PowerSwitch', Cmd[1])):
					if (isSpecialCAPICommand(Cmd)):
						return False
					else:
						errorLog.append("Syntax error on line %d: %s is not a valid CAPI Command" % (lineNumber, orginalLine))
						totalSyntaxErrors += 1
						return True
			elif (Cmd[0] == "wfa_adept_control_agent" or Cmd[0] == "$wfa_tester_control_agent"):
				if (isSpecialCAPICommand(Cmd)):
					return False
			elif (Cmd[0] == "wfa_sniffer"):
				if (isMultipleReturnCAPICommand(Cmd)):
					return False
				elif (isDoubleReturnCAPICommand(Cmd)):
					return False
			elif (re.search(r'^wfa_', Cmd[0]) and re.search(r'_get_info$', Cmd[1])):
				if (isMultipleReturnCAPICommand(Cmd)):
					return False
			elif (Cmd[0] == "wfa_console_ctrl" or Cmd[0] == "$SS1_control_agent"):
				if (isDoubleReturnCAPICommand(Cmd)):
					return False
			elif (Cmd[0] == "wfa_control_agent_dut" or re.match(r'\$STA\d_control_agent', Cmd[0])):
				if (isMultipleReturnCAPICommand(Cmd)):
					return False
			if (Cmd[0] == "TestbedAPConfigServer" or re.search(r'^wfa_' , Cmd[0]) or (Cmd[0][0] == '$')):
				if (isNormalCAPICommand(Cmd)):
					return False
				errorLog.append("Syntax error on line %d: %s is not a valid CAPI Command" % (lineNumber, orginalLine))
				totalSyntaxErrors += 1
				return True
		#root[5] is for all other commands with >= 3 '!'s; content is not checked
		for element in root[5].iter():
				if element.find(Cmd[0]):
					return False
		errorLog.append("Syntax error on line %d: %s is not a known command" % (lineNumber, orginalLine))
		totalSyntaxErrors += 1
		return True

def checkFile(fileObj, name, root):
	errorLog = []
	lineNumber = 1 
	with open(fileObj, 'r') as filePtr:
		for line in filePtr:
			#Check if line is a comment or blank
			if (line[0] == '#' or line.strip() == ''):
				lineNumber += 1
				continue
			#Parse the line and check syntax
			else:
				line = line.strip('\r\n')
				checkLine(line, lineNumber, errorLog, name)
				lineNumber += 1
	if (len(errorLog)):
		print "Syntax error(s) were found in file " + name + " in directory " + os.path.basename(os.path.dirname(os.path.join(root, name)))
		for error in errorLog:
			print error
		print ""

def openFiles(testCase):
	testCase = "WTS-" + testCase  
	numOfFiles = 0
	for root, dirs, files in os.walk(cmdspath):
		if (os.path.basename(root) == testCase):
			for name in files:
				#Don't check files that are formatted differently; it will just result in parsing errors
				if (re.search(r'\.xml$', name)):
					continue
				if (name in fileSkipList[testCase]):
					continue
				checkFile(os.path.join(root, name), name, root)
				numOfFiles += 1
	print "Number of files scanned: " + str(numOfFiles) 

def main():
	supportedList = ["11n", "P2P", "VHT", "WFD", "WFDS", "PMF", "HS2", "HS2-R2", "WMMPS", "NAN"]
	print "Enter the test case you wish to check from the following list"
	while (True):
		print "Currently supported:",
		for case in supportedList:
			if (not (case == supportedList[len(supportedList)-1])):
				print "%s |" % (case),
			else:
				print "%s" % (case)
		testCase = raw_input('')
		if testCase in supportedList:
			break
		else:
			print "That test case is not currently supported"
	sys.stdout = open('SyntaxLogFile.txt', 'w') 
	openFiles(testCase)
	print "Program completed with (at least) " + str(totalSyntaxErrors) + " syntax errors found"
	sys.stdout = sys.__stdout__
	print "Program completed - see \'SyntaxLogFile.txt\' for results"

if __name__ == '__main__':
	main()