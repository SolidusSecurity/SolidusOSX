import SolidusErrorLog

import datetime
import urllib, urllib2
from xml.dom import minidom
import socket
import uuid
import platform
import sys
import os
import base64

#!TFinish 1.0 - Move this into a helper module and error handle
strApplicationDirectory = os.path.dirname(os.path.realpath(__file__)) + "/"
XML_LOG_FILE_NAME = "EventLog.xml"
XML_LOG_FILE = strApplicationDirectory + XML_LOG_FILE_NAME

XML_LOG_REPORTING_TRACKER_FILE_NAME = "ReportingTracker.dat"
XML_LOG_REPORTING_TRACKER_FILE = strApplicationDirectory + XML_LOG_REPORTING_TRACKER_FILE_NAME

LOCMOD_ENTRY_TYPE_FILE_VALUE = "4"
LOCMOD_ENTRY_TYPE_FOLDER_VALUE = "5"

SPLUNK_REST_SERVER = "https://SolidusSecurity.com"
SPLUNK_REST_SERVER_PORT = 8089
SPLUNK_REST_SERVER_WITH_PORT = SPLUNK_REST_SERVER + ":" + str(SPLUNK_REST_SERVER_PORT)

def openXMLLogFile(strModeIn):
    return open(XML_LOG_FILE, strModeIn)

def addEventIDAndTimeToInnerEventXML(strInnerEventXmlIn):

    strEventGuid = str(uuid.uuid4())
    #We round to 3 places (milliseconds) for consistency with Windows endpoints
    strEventTime = datetime.datetime.utcnow().isoformat()[:-3]
            
    strXmlRet = "<Event><ID>" + strEventGuid + "</ID>" + \
                "<DateTime>" + strEventTime + "</DateTime>" + \
                strInnerEventXmlIn + \
                "</Event>"

    return strXmlRet

def writeLine(strEventIn):
    try:
        outFile = openXMLLogFile("a")
        outFile.write(strEventIn + "\n")
        outFile.close()
    #Not much we can do here other than log the failure
    except Exception as err:
        SolidusErrorLog.logError(str(err), "SolidusXMLLog::writeLine")
        
def writeDirectoryLocPermitFileEvent(strLocGuidIn, strEntryNameIn):
    writeDirectoryLocPermitEvent(strLocGuidIn, LOCMOD_ENTRY_TYPE_FILE_VALUE, strEntryNameIn)

def writeDirectoryLocPermitDirectoryEvent(strLocGuidIn, strEntryNameIn):
    writeDirectoryLocPermitEvent(strLocGuidIn, LOCMOD_ENTRY_TYPE_FOLDER_VALUE, strEntryNameIn)
        
def writeDirectoryLocPermitEvent(strLocGuidIn, strEntryTypeIn, strEntryNameIn):
    try:
            
        strEvent = "<LocMod>" + \
                   "<LocModType>" + "Permit" + "</LocModType>" + \
                   "<Location><LocGuid>" + strLocGuidIn + "</LocGuid></Location>" + \
                   "<LocEntry>" + \
                   "<EntryType>" + strEntryTypeIn + "</EntryType>" + \
                   "<EntryName>" + strEntryNameIn + "</EntryName>" + \
                   "</LocEntry><Mode><ModeEnum>1</ModeEnum></Mode>" + \
                   "</LocMod>"

        strEvent = addEventIDAndTimeToInnerEventXML(strEvent)
        writeLine(strEvent)

    #Not much we can do here other than log the failure
    except Exception as err:
        SolidusErrorLog.logError(str(err), "SolidusXMLLog::writeDirectoryLocPermitEvent")

def writeOriginInfoEvent(strOriginRegisteredEmailIn):
    try:
            
        #!TFinish 1.0 - Add support for Hard Drive Serial
        strHardDriveSerialNumber = ""

        try:
            lstFQDN = socket.getfqdn().split(".")
            strDomainName = lstFQDN[1]
            strComputerName = lstFQDN[0]
        except:
            strDomainName = ""
            strComputerName = socket.getfqdn()
                     
        if (sys.maxsize > 2**32):
            strArchitecture = "64"
        else:
            strArchitecture = "32"


        lstVersionNumber = platform.release().split(".")
        
        strMajorVersion = lstVersionNumber[0]
        strMinorVersion = lstVersionNumber[1]
        strServicePackMajor = "0"
        strServicePackMinor = "0"
        
        #!TFinish 1.0 - Tie this to agent version number properly
        SOLIDUS_VERSION_NUMBER_STRING = "0.10"
        
        try:
            strPublicIPAddress = urllib2.urlopen("http://myexternalip.com/raw").read().strip()
        #Just end a blank IP Address if we can't retrieve it
        except:
            strPublicIPAddress = ""
                
        strEvent = "<OriginInfo>" + \
                   "<HardDriveSerial>" + strHardDriveSerialNumber + "</HardDriveSerial>" + \
                   "<DomainName>" + strDomainName + "</DomainName>" + \
                   "<ComputerName>" + strComputerName + "</ComputerName>" + \
                   "<ContactEmailAddress>" + strOriginRegisteredEmailIn + "</ContactEmailAddress>" + \
                   "<OS>OSX</OS>" + \
                   "<OSArchitecture>" + strArchitecture + "</OSArchitecture>" + \
                   "<OSInfo>" + \
                   "<MajorVersion>" + strMajorVersion + "</MajorVersion>" + \
                   "<MinorVersion>" + strMinorVersion + "</MinorVersion>" + \
                   "<SPMajorVersion>" + strServicePackMajor + "</SPMajorVersion>" + \
                   "<SPMinorVersion>" + strServicePackMinor + "</SPMinorVersion>" + \
                   "</OSInfo>" + \
                   "<SolidusAgentVersion>" + SOLIDUS_VERSION_NUMBER_STRING + "</SolidusAgentVersion>" + \
                   "<SolidusReporterVersion>" + SOLIDUS_VERSION_NUMBER_STRING + "</SolidusReporterVersion>" + \
                   "<PublicIPAdress>" + strPublicIPAddress + "</PublicIPAdress>" + \
                   "</OriginInfo>"

        strEvent = addEventIDAndTimeToInnerEventXML(strEvent)
        writeLine(strEvent)
        
    #Not much we can do here other than log the failure
    except Exception as err:
        SolidusErrorLog.logError(str(err), "SolidusXMLLog::writeOriginInfoEvent")

def getPreviouslyReportedLineCountFromReportingTrackerFile():
    #Get the count of previously reported events to advance ahead in the XML Log File    
    try:
        inFile = open(XML_LOG_REPORTING_TRACKER_FILE, "r")
        return int(inFile.readline().rstrip("\n"))

    #If we can't read the file in, we are forced to resend all the events                                           
    except Exception as err:
        #Log an error if the file existed but the tracker file read in failed (missing file expected at times)
        try:
            if (os.path.exists(XML_LOG_REPORTING_TRACKER_FILE)):
                SolidusErrorLog.logError(str(err), "SolidusXMLLog::getPreviouslyReportedLineCountFromReportingTrackerFile")
   
        #Ignore if any error is encountered since this is just for logging
        except:
            pass
        
        return 0

def writeOutReportingTrackerFile(nPreviouslyReportedLineCountIn):
    try:
        outFile = open(XML_LOG_REPORTING_TRACKER_FILE, "w")
        outFile.write(str(nPreviouslyReportedLineCountIn))
        outFile.close()

    #We can log this and hope the next call overwrites it with the proper info - otherwise worst case is we resend events
    except Exception as err:
        SolidusErrorLog.logError(str(err), "SolidusXMLLog::writeOutReportingTrackerFile")

class SolidusSplunkError(Exception):
    pass

def loginToSplunkForReporting():

    try:
        strSplunk1 = "AgentAPI"
        strSplunk2 = base64.b64decode("fihzYXA4VyJoJSQ8VyZeXQ==")
        strSplunkSessionPath = "/services/auth/login"
        SPLUNK_SESSION_KEY_FIELD_NAME = "sessionKey"
        SPLUNK_AUTHORIZATION_FIELD_NAME = "Authorization"
        SPLUNK_AUTHORIZATION_TYPE_SPLUNK_FIELD_NAME = "Splunk"
        
        strSplunkUrl = SPLUNK_REST_SERVER_WITH_PORT + strSplunkSessionPath
        request = urllib2.Request(strSplunkUrl,
                                  data=urllib.urlencode({"username": strSplunk1, "password": strSplunk2}))

        response = urllib2.urlopen(request)
        strSessionKey = minidom.parseString(response.read()).getElementsByTagName(SPLUNK_SESSION_KEY_FIELD_NAME)[0].childNodes[0].nodeValue

        return { SPLUNK_AUTHORIZATION_FIELD_NAME: SPLUNK_AUTHORIZATION_TYPE_SPLUNK_FIELD_NAME + ' %s' % strSessionKey }

    except Exception as err:
        #!TFinish 1.0 - Determine whether we want to always log this or only under certain circumstances
        SolidusErrorLog.logError(str(err), "SolidusXMLLog::loginToSplunkForReporting")
        raise SolidusSplunkError(str(err))
                                     
def reportEvents(headerSplunkIn, strEventsIn, strOriginGuidIn):

    try:
        strSimpleReceiverRootUrl = SPLUNK_REST_SERVER_WITH_PORT + "/services/receivers/simple"
        paramsReceiver = { "host":strOriginGuidIn, "sourcetype":"SolidusEventXml", "index":"solidus_event_osx"}
        
        #Encode to match the props.conf for SolidusEventXml (UNICODELITTLE) and decode to ISO-8859-1 for requests transmit over the wire
        strEventsIn = strEventsIn.encode("utf-16-le", "replace").decode("iso-8859-1", "replace")

        request = urllib2.Request(strSimpleReceiverRootUrl + "?" + urllib.urlencode(paramsReceiver),
                                  data=strEventsIn,
                                  headers=headerSplunkIn)

        #This will throw an exception if an error is encountered
        urllib2.urlopen(request)

    except Exception as err:
        #!TFinish 1.0 - Determine whether we want to always log this or only under certain circumstances
        SolidusErrorLog.logError(str(err), "SolidusXMLLog::reportEvents")
        raise SolidusSplunkError(str(err))
            
def reportAllEvents(strOriginGuidIn):

    try:
        headerSplunk = loginToSplunkForReporting()
        
        nPreviouslyReportedLineCount = getPreviouslyReportedLineCountFromReportingTrackerFile()
        
        inFile = openXMLLogFile("r")

        nBufferedEvents = 0
        nMaxBufferedEvents = 256
        strBufferedEvents = ""
        
        nLineCount = 0
        while (True):

            #Intentionally keep the newline as part of the read-in string so we can combine events
            strLine = inFile.readline()

            if (len(strLine) == 0):
                break

            nLineCount += 1

            #Skip previously reported lines
            if (nLineCount <= nPreviouslyReportedLineCount):
                continue

            nBufferedEvents += 1
            strBufferedEvents += strLine
                
            if (nBufferedEvents >= nMaxBufferedEvents):
                reportEvents(headerSplunk, strBufferedEvents, strOriginGuidIn)
                writeOutReportingTrackerFile(nLineCount)
                nBufferedEvents = 0
                strBufferedEvents = ""

        if (nBufferedEvents > 0):
            reportEvents(headerSplunk, strBufferedEvents, strOriginGuidIn)
            writeOutReportingTrackerFile(nLineCount)
            nBufferedEvents = 0
            strBufferedEvents = ""
            
        inFile.close()

    #If this fails, we'll just have to attempt to send it again later
    except SolidusSplunkError:
        #!TFinish 1.0 - Determine whether we want to always log this or only under certain circumstances
        SolidusErrorLog.logError("Reporting Failed", "SolidusXMLLog::reportAllEvents")
    except Exception as err:
        #!TFinish 1.0 - Determine whether we want to always log this or only under certain circumstances
        SolidusErrorLog.logError("Reporting Failed: " + str(err), "SolidusXMLLog::reportAllEvents")
                                 
