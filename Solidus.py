import SolidusXMLLog

#!TRemove - When you shift the examples to the right files
import datetime
import shutil
import os
import hashlib
import urllib, urllib2
from xml.dom import minidom
import base64
import socket
import uuid
import platform
import sys


def getFileMD5(strFileIn):
    try:
        md5 = hashlib.md5()
        with open(strFileIn, "rb") as inFile:
                #!TFinish - Add Stackoverflow comment referencing this as optimal size
                for bytesCurrent in iter(lambda: inFile.read(65536), b""):
                        md5.update(bytesCurrent)

        return md5.hexdigest()

    except:
        #!TFinish - Add Error Handling and remove raise
        raise
        pass
                        

class OSXLocEntry:

    strEntryName = ""

    @classmethod
    def initFromFile(cls, inFileIn):
        clsRet = cls("")
        clsRet.readFromFile(inFileIn)
        return clsRet
    
    def __init__(self, strEntryNameIn):
        self.strEntryName = strEntryNameIn

    def getEntryDictKey(self):
        return self.strEntryName

    def writeToFile(self, outFileIn):
        outFileIn.write(self.strEntryName)

    def readFromFile(self, inFileIn):
        self.strEntryName = inFileIn.readline().rstrip("\n")


class OSXLocFileOrDirectoryEntry:

    strEntryName = ""
    nFileOrDirectory = -1

    ENTRY_IS_DIR_VALUE = 0
    ENTRY_IS_FILE_VALUE = 1
    
    @classmethod
    def initFromFile(cls, inFileIn):
        clsRet = cls("", -1)
        clsRet.readFromFile(inFileIn)
        return clsRet

    @classmethod
    def initForDirectory(cls, strDirectoryNameIn):
        return cls(strDirectoryNameIn, cls.ENTRY_IS_DIR_VALUE)               

    @classmethod
    def initForFile(cls, strFileNameIn):
        return cls(strFileNameIn, cls.ENTRY_IS_FILE_VALUE)               
    
    def __init__(self, strEntryNameIn, nFileOrDirectoryIn):
        self.strEntryName = strEntryNameIn
        self.nFileOrDirectory = nFileOrDirectoryIn

    def getEntryDictKey(self):
        return self.strEntryName

    def writeToFile(self, outFileIn):
        outFileIn.write(self.strEntryName)
        outFileIn.write("\n")
        outFileIn.write(str(self.nFileOrDirectory))
            
    def readFromFile(self, inFileIn):
        self.strEntryName = inFileIn.readline().rstrip("\n")
        self.nFileOrDirectory = int(inFileIn.readline().rstrip("\n"))
                
                  
class OSXDirectoryLocClass:

    strDirectory = ""
    str32BitLocGuid = ""
    str64BitLocGuid = ""
    strRGFFile = ""
    strRGFBackupFile = ""
    dictOSXLocEntries = {}

    def __init__(self):
        pass
            
    def __init__(self, strDirectoryIn, str32BitLocGuidIn, str64BitLocGuidIn, strRGFFileIn, strRGFBackupFileIn, bInitForInstallSave):
        self.strDirectory = strDirectoryIn
        self.str32BitLocGuid = str32BitLocGuidIn
        self.str64BitLocGuid = str64BitLocGuidIn
        self.strRGFFile = strRGFFileIn
        self.strRGFBackupFile = strRGFBackupFileIn

        if (not bInitForInstallSave):
            self.readFromFile()
            
    def writeToFile(self):
        try:
            strTempFile = self.strRGFFile + ".tmp"

            outFile = open(strTempFile, "w")
            outFile.write(str(len(self.dictOSXLocEntries)) + "\n")
            for key, entry in self.dictOSXLocEntries.iteritems():
                entry.writeToFile(outFile)
                outFile.write("\n")
                    
            outFile.close()

            shutil.move(strTempFile, self.strRGFFile)
            
            pass
        
        except:
            #!TFinish - Add Error Handling
            raise
            pass
    
    def readFromFile(self):
        try:
            if (len(self.dictOSXLocEntries) != 0):
                pass
                #!TFinish Add error message and raise error
            
            inFile = open(self.strRGFFile, "r")
            nEntryCount = int(inFile.readline())
            
            for ignore in range(0, nEntryCount):
                currentEntry = OSXLocFileOrDirectoryEntry.initFromFile(inFile)
                self.dictOSXLocEntries[currentEntry.getEntryDictKey()] = currentEntry
                    
            inFile.close()


        except:
            #!TFinish - Add Error Handling and remove raise
            raise
            pass
                    
    def addOSXLocEntry(self, osxLocEntryIn):
        self.dictOSXLocEntries[osxLocEntryIn.getEntryDictKey()] = osxLocEntryIn

    def addOSXLocDirectoryEntry(self, strDirectoryNameIn):
        self.addOSXLocEntry(OSXLocFileOrDirectoryEntry.initForDirectory(strDirectoryNameIn))

    def entryExists(self, strEntryNameIn):
        return (strEntryNameIn in self.dictOSXLocEntries)

    def saveForInstall(self):
        #Create RGF Data Directory
        strRGFDataDirectory = os.path.dirname(self.strRGFFile)
        if (not os.path.exists(strRGFDataDirectory)):
                os.makedirs(strRGFDataDirectory)
                
        self.evaluate()
        self.writeToFile()
            
    def evaluate(self):
##        for strCurrentDirectory, lstSubDirectories, lstFiles in os.walk(strDirectory):
##                for strSubDirectory in lstSubDirectories:
##                        print ("Sub:", strSubDirectory)
##                        
##                for strFile in lstFiles:
##                        print (strFile)

        for strFile in os.listdir(self.strDirectory):

            if (os.path.isfile(strFile)):
                print("File:", strFile)
            else:
                if (not self.entryExists(strFile)):
                    self.addOSXLocDirectoryEntry(strFile)
                    #We always use the 64Bit Loc GUID
                    SolidusXMLLog.writeDirectoryLocPermitDirectoryEvent(self.str64BitLocGuid, strFile)

                

class LocationsManager():

    lstLocations = []

    strApplicationPath = ""
    LOC_FILE_APPLICATION_DIRECTORY_REPLACEABLE_PARAM = "%ApplicationDirectory%"

    def __init__(self, bInitForInstallIn):
        self.readInLocationsFile(bInitForInstallIn)
        #!TFinish - Add Error Handling

    def readInLocationsFile(self, bInitForInstallIn):
        try:
            self.strApplicationPath = os.path.dirname(os.path.realpath(__file__)) + "/"
            strLocationsFileName = "OSXLocations.txt"
            LOC_FILE_DELIMITER = "|"
            
            LOC_FILE_DIRECTORY_LOC_VALUE = "Directory"
            
            inFile = open(self.strApplicationPath + strLocationsFileName, "r")

            #!TFinish 1.0 - Add File Version Check
            inFile.readline()

            #Read in the Locations
            while (True):
                strCurrentLoc = inFile.readline()
                if (len(strCurrentLoc) == 0):
                    break

                if (strCurrentLoc.startswith("#")):
                    continue

                
                lstFields = strCurrentLoc.split(LOC_FILE_DELIMITER)

                self.setupDirectoryLocation(lstFields, bInitForInstallIn)
                
        #!TFinish - Add Error Handling
        except:
                raise

    def setupDirectoryLocation(self, lstFieldsIn, bInitForInstallIn):
        MODE_COUNT = 4
        DIRECTORY_FIELD_COUNT = MODE_COUNT + 13

        COMPATIBILITY_FIELD = 1
        FIRST_MODE_FIELD = 2
        FIRST_FIELD_AFTER_MODES = FIRST_MODE_FIELD + MODE_COUNT

        LOCATION_GUID_32BIT_FIELD = 0 + FIRST_FIELD_AFTER_MODES
        LOCATION_GUID_64BIT_FIELD = 1 + FIRST_FIELD_AFTER_MODES
        LOCATION_AUTOEXEC_FILE_INFO_TYPE_FIELD = 2 + FIRST_FIELD_AFTER_MODES
        LOCATION_EXECUTION_TYPE_FIELD = 3 + FIRST_FIELD_AFTER_MODES
        LOCATION_IS_MALWARE_PERCENT_FIELD = 4 + FIRST_FIELD_AFTER_MODES
        LOCATION_MALWARE_USES_LOCATION_PERCENT_FIELD = 5 + FIRST_FIELD_AFTER_MODES
        DIRECTORY_PATH_FIELD = 6 + FIRST_FIELD_AFTER_MODES
        RGF_COUNT_FIELD = 7 + FIRST_FIELD_AFTER_MODES
        WHITELIST_COUNT_FIELD = 8 + FIRST_FIELD_AFTER_MODES
        BLACKLIST_COUNT_FIELD = 9 + FIRST_FIELD_AFTER_MODES
        EXCEPTION_COUNT_FIELD = 10 + FIRST_FIELD_AFTER_MODES

        #Verify the right number of fields are in the entry
        nRGFFilesCount = int(lstFieldsIn[RGF_COUNT_FIELD])

        nWhitelistCountFieldIndex = WHITELIST_COUNT_FIELD + nRGFFilesCount
        nWhitelistCount = int(lstFieldsIn[nWhitelistCountFieldIndex])

        nBlacklistCountFieldIndex = BLACKLIST_COUNT_FIELD + nRGFFilesCount + nWhitelistCount
        nBlacklistCount = int(lstFieldsIn[nBlacklistCountFieldIndex])

        nExceptionCountFieldIndex = EXCEPTION_COUNT_FIELD + nRGFFilesCount + nWhitelistCount + nBlacklistCount
        nExceptionsCount = int(lstFieldsIn[nExceptionCountFieldIndex])

        if (len(lstFieldsIn) != (DIRECTORY_FIELD_COUNT + nRGFFilesCount + nWhitelistCount + nBlacklistCount + nExceptionsCount)):
            #!TFinish - Replace this with proper exception and logging
            raise Exception ("Invalid Location Entry")

        str32BitLocGuid = lstFieldsIn[LOCATION_GUID_32BIT_FIELD]
        str64BitLocGuid = lstFieldsIn[LOCATION_GUID_64BIT_FIELD]

        strDirectory = lstFieldsIn[DIRECTORY_PATH_FIELD]

        #We only support an RGF and Backup RGF
        if (nRGFFilesCount != 2):
            #!TFinish - Replace this with proper exception and logging
            raise Exception ("Invalid RGF Count")

        
        strRGFFile = lstFieldsIn[RGF_COUNT_FIELD + 1]
        strRGFBackupFile = lstFieldsIn[RGF_COUNT_FIELD + 2]

        strRGFFile = strRGFFile.replace(self.LOC_FILE_APPLICATION_DIRECTORY_REPLACEABLE_PARAM, self.strApplicationPath[:-1])
        strRGFBackupFile = strRGFBackupFile.replace(self.LOC_FILE_APPLICATION_DIRECTORY_REPLACEABLE_PARAM, self.strApplicationPath[:-1])
        
        
        self.lstLocations.append(OSXDirectoryLocClass(strDirectory, str32BitLocGuid, str64BitLocGuid, strRGFFile, strRGFBackupFile, bInitForInstallIn))


    def install(self):
        try:
            for loc in self.lstLocations:
                loc.saveForInstall()

        #!TFinish - Add Error Handling
        except:
            raise

    def evaluateAllLocations(self):
        try:
            for loc in self.lstLocations:
                loc.evaluate()

        #!TFinish - Add Error Handling
        except:
            raise

#!TFinish - Move these to the right location
strApplicationPath = os.path.dirname(os.path.realpath(__file__)) + "/"
SOLIDUS_CONFIG_FILE_NAME = "Solidus.config"
SOLIDUS_CONFIG_FILE = strApplicationPath + SOLIDUS_CONFIG_FILE_NAME
                         
def writeSolidusConfigFile(strEmailAddressIn):
    try:
        outFile = open(SOLIDUS_CONFIG_FILE, "w")
        #!TFinish - Tie this to agent version number properly
        outFile.write("Solidus Config File Version .1\n")
        outFile.write(strEmailAddressIn + "\n")
        outFile.close()
    except:
        #!TFinish - Add Error Handling
        raise
                         
def getSolidusRegisteredEmailAddress():

    try:        
        inFile = open(SOLIDUS_CONFIG_FILE, "r")

        #Ignore the version header at this time
        strFileVersionHeader = inFile.readline()

        strEmailAddress = inFile.readline().rstrip("\n")

        if (len(strEmailAddress) == 0):
            #!TFinish - Add Logging?
            raise Exception()
            

        return strEmailAddress
                         
    #We need to reinstall if the config file does not exist or does not match what we expect
    except:
        return None


def installSolidus():

    #!TFinish - Add Error Handling
    strEmailAddress = raw_input("Please Enter Your Valid Email Address: ")
    strEmailAgain = raw_input("Please Enter Your Email Address Again: ")

    if (strEmailAddress.lower() != strEmailAgain.lower()):
        print ("Install Failed: The email addresses did not match.")
        #!TFinish - Add Error Handling and Logging
        return

    strEmailAddress = strEmailAddress.strip()
    writeSolidusConfigFile(strEmailAddress)
    
    locManager = LocationsManager(True)
    locManager.install()


def test():

    strEmailAddress = getSolidusRegisteredEmailAddress()

    if (strEmailAddress is None):
        strEmailAddress = installSolidus()

    SolidusXMLLog.writeOriginInfoEvent(strEmailAddress)
    return
    
    locManager = LocationsManager(False)
    locManager.evaluateAllLocations()
    SolidusXMLLog.reportAllEvents()
    return

    print (str(uuid.uuid4()))
    print (str(uuid.uuid4()))
    return 
    
    osxLocClass = OSXDirectoryLocClass("/Users/hhempste/Documents/python/FirstLoc.rgf")
    try:
            osxLocClass.readFromFile()
    except:
            pass
    
    evaluateDirectory(osxLocClass, "/System/Library/Extensions/")
    osxLocClass.writeToFile()
    return
    
    #osxLocClass.addOSXLocEntry(OSXLocEntry("Test1"))
    #osxLocClass.addOSXLocEntry(OSXLocEntry("Test2"))
    #osxLocClass.writeToFile()
    osxLocClass.readFromFile()
    #!TRemove - All Below
    print 
    print (os.path.getsize("/Users/hhempste/Documents/python/FirstLoc.rgf"))
    print (getFileMD5("/Users/hhempste/Documents/python/FirstLoc.rgf"))
    print (base64.b64encode('~(sap8W"h%$<W&^]'))
    print (base64.b64decode("fihzYXA4VyJoJSQ8VyZeXQ=="))

    print(buildOriginInfoEvent())
    return
    
    strSplunk1 = "AgentAPI"
    strSplunk2 = base64.b64decode("fihzYXA4VyJoJSQ8VyZeXQ==")
    strRootSplunkAddress = "https://SolidusSecurity.com"
    strSplunkSessionPath = "/services/auth/login"
    nSplunkPort = 8089
    SPLUNK_SESSION_KEY_FIELD_NAME = "sessionKey"
    
    strSplunkUrl = strRootSplunkAddress + ":" + str(nSplunkPort) + strSplunkSessionPath
    print (strSplunkUrl)
    request = urllib2.Request(strSplunkUrl,
                              data=urllib.urlencode({"username": strSplunk1, "password": strSplunk2}))

    response = urllib2.urlopen(request)
    strSessionKey = minidom.parseString(response.read()).getElementsByTagName(SPLUNK_SESSION_KEY_FIELD_NAME)[0].childNodes[0].nodeValue
    print (strSessionKey)


test()

        
        
