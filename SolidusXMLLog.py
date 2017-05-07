import datetime
import urllib2
import socket
import uuid
import platform
import sys
import os

strApplicationDirectory = os.path.dirname(os.path.realpath(__file__)) + "/"
XML_LOG_FILE_NAME = "EventLog.xml"
strXMLLogFile = strApplicationDirectory + XML_LOG_FILE_NAME

XML_LOG_REPORTING_TRACKER_FILE_NAME = "ReportingTracker.dat"
strReportingTrackerFile = strApplicationDirectory + XML_LOG_REPORTING_TRACKER_FILE_NAME

LOCMOD_ENTRY_TYPE_FILE_VALUE = "4"
LOCMOD_ENTRY_TYPE_FOLDER_VALUE = "5"

def openXMLLogFile(strModeIn):
    return open(strXMLLogFile, strModeIn)


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
    #!TFinish - Add Error Handling
    outFile = openXMLLogFile("a")
    outFile.write(strEventIn + "\n")
    outFile.close()

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
            
    except:
        #!TFinish - Add Error Handling
        raise

def writeOriginInfoEvent(strOriginRegisteredEmailIn):
    try:
            
        #!TFinish - Add support for this
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
        
        #!TFinish - Move this
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
        
    except:
        pass
        #!TFinish - Add Error Handling
        raise

def getPreviouslyReportedLineCountFromReportingTrackerFile():
    #Get the count of previously reported events to advance ahead in the XML Log File    
    try:
        inFile = open(strReportingTrackerFile)
        return int(inFile.readline().rstrip("\n"))

    #If we can't read the file in, we are forced to resend all the events                                           
    except:
        return 0

def writeOutReportingTrackerFile(nPreviouslyReportedLineCountIn):
    try:
        outFile = open(strReportingTrackerFile, "w")
        outFile.write(str(nPreviouslyReportedLineCountIn))
        outFile.close()
        
    except:
        #!TFinish - Add Error Handling and Logging
        raise

def reportEvents(strEventsIn):
    #!TRemove NOW
    print (strEventsIn)
    
    pass

def reportAllEvents():

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
            reportEvents(strBufferedEvents)
            writeOutReportingTrackerFile(nLineCount)
            nBufferedEvents = 0
            strBufferedEvents = ""

    if (nBufferedEvents > 0):
        reportEvents(strBufferedEvents)
        writeOutReportingTrackerFile(nLineCount)
        nBufferedEvents = 0
        strBufferedEvents = ""
        
    inFile.close()
        
def test():
    pass
    #writeOriginInfoEvent()
    #writeDirectoryLocPermitDirectoryEvent("TestGuid", "TestDirectory")
    
if __name__ == "__main__":
    test()
