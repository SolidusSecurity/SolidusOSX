import SolidusErrorLog
import SolidusConfigFile
import SolidusXMLLog
import sys
import uuid
import shutil
import os

#All Exceptions Pass Through
#!TFinish 1.0 - Add More Robust Function by Function Error Handling
class OSXLocEntry:

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

#All Exceptions Pass Through
#!TFinish 1.0 - Add More Robust Function by Function Error Handling
class OSXLocFileOrDirectoryEntry:

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

class OSXDirectoryLocClassError(Exception):
    pass

#!TFinish 1.0 - Add More Robust Function by Function Error Handling
class OSXDirectoryLocClass:
            
    def __init__(self, strDirectoryIn, str32BitLocGuidIn, str64BitLocGuidIn, strRGFFileIn, strRGFBackupFileIn, bInitForInstallSave):
        self.strDirectory = strDirectoryIn
        self.str32BitLocGuid = str32BitLocGuidIn
        self.str64BitLocGuid = str64BitLocGuidIn
        self.strRGFFile = strRGFFileIn
        self.strRGFBackupFile = strRGFBackupFileIn
        self.dictOSXLocEntries = {}
        
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
        
        except Exception as err:
            SolidusErrorLog.logError(str(err), "OSXDirectoryLocClass::writeToFile")
            raise OSXDirectoryLocClassError(str(err))
    
    def readFromFile(self):
        try:
            #This is an unexpected condition that indicates a code mistake error
            if (len(self.dictOSXLocEntries) != 0):
                #We keep the old entries to be overly inclusive rather than risk omitting something that needs to be there
                SolidusErrorLog.logCodeMistakeError("Dictionary Not Empty", "OSXDirectoryLocClass::readFromFile")
            
            inFile = open(self.strRGFFile, "r")
            nEntryCount = int(inFile.readline())
            
            for ignore in range(0, nEntryCount):
                currentEntry = OSXLocFileOrDirectoryEntry.initFromFile(inFile)
                self.dictOSXLocEntries[currentEntry.getEntryDictKey()] = currentEntry
                    
            inFile.close()

        except Exception as err:
            SolidusErrorLog.logError(str(err), "OSXDirectoryLocClass::readFromFile")
            raise OSXDirectoryLocClassError(str(err))
                    
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
        for strFile in os.listdir(self.strDirectory):

            if (os.path.isfile(strFile)):
                print("File:", strFile)
            else:
                if (not self.entryExists(strFile)):
                    self.addOSXLocDirectoryEntry(strFile)
                    #We always use the 64Bit Loc GUID
                    SolidusXMLLog.writeDirectoryLocPermitDirectoryEvent(self.str64BitLocGuid, strFile)

class LocationsManagerError(Exception):
    pass

#!TFinish 1.0 - Add More Robust Function by Function Error Handling
class LocationsManager():

    LOC_FILE_APPLICATION_DIRECTORY_REPLACEABLE_PARAM = "%ApplicationDirectory%"

    def __init__(self, bInitForInstallIn):
        self.lstLocations = []
        self.readInLocationsFile(bInitForInstallIn)

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

            return
        
        #Function exception raised below individual handlers
        except LocationsManagerError:
            #Already Logged
            pass

        except Exception as err:
            SolidusErrorLog.logError(str(err), "LocationsManager::readInLocationsFile")
            
        raise LocationsManagerError("Read In Locations File Failed")

    def setupDirectoryLocation(self, lstFieldsIn, bInitForInstallIn):

        try:
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
                SolidusErrorLog.logCodeMistakeError("Invalid Location Entry", "LocationsManager::setupDirectoryLocation")
                raise LocationsManagerError("Invalid Location Entry")

            str32BitLocGuid = lstFieldsIn[LOCATION_GUID_32BIT_FIELD]
            str64BitLocGuid = lstFieldsIn[LOCATION_GUID_64BIT_FIELD]

            strDirectory = lstFieldsIn[DIRECTORY_PATH_FIELD]

            #We only support an RGF and Backup RGF
            if (nRGFFilesCount != 2):
                SolidusErrorLog.logCodeMistakeError("Invalid RGF Count", "LocationsManager::setupDirectoryLocation")
                raise LocationsManagerError("Invalid RGF Count")
            
            strRGFFile = lstFieldsIn[RGF_COUNT_FIELD + 1]
            strRGFBackupFile = lstFieldsIn[RGF_COUNT_FIELD + 2]

            strRGFFile = strRGFFile.replace(self.LOC_FILE_APPLICATION_DIRECTORY_REPLACEABLE_PARAM, self.strApplicationPath[:-1])
            strRGFBackupFile = strRGFBackupFile.replace(self.LOC_FILE_APPLICATION_DIRECTORY_REPLACEABLE_PARAM, self.strApplicationPath[:-1])
            
            self.lstLocations.append(OSXDirectoryLocClass(strDirectory, str32BitLocGuid, str64BitLocGuid, strRGFFile, strRGFBackupFile, bInitForInstallIn))

        except LocationsManagerError:
            #Already Logged
            raise
        except Exception as err:
            SolidusErrorLog.logError(str(err), "LocationsManager::setupDirectoryLocation")
            raise LocationsManagerError(str(err))

    def install(self):
        try:
            for loc in self.lstLocations:
                loc.saveForInstall()

        except LocationsManagerError:
            SolidusErrorLog.logError("Save Failed", "LocationsManager::install")
            raise
        except Exception as err:
            SolidusErrorLog.logError(str(err), "LocationsManager::install")
            raise LocationsManagerError(str(err))

    def evaluateAllLocations(self):
        try:
            for loc in self.lstLocations:
                loc.evaluate()
        except LocationsManagerError:
            SolidusErrorLog.logError("Evaluate Failed", "LocationsManager::evaluateAllLocations")
            raise
        except Exception as err:
            SolidusErrorLog.logError(str(err), "LocationsManager::evaluateAllLocations")
            raise LocationsManagerError(str(err))

def installSolidus():

    try:
        strOriginGuid = str(uuid.uuid4())

        #!TFinish - Add Error Handling
        strEmailAddress = raw_input("Please Enter Your Valid Email Address: ")
        strEmailAgain = raw_input("Please Enter Your Email Address Again: ")

        if (strEmailAddress.lower() != strEmailAgain.lower()):
            sys.exit("INSTALL FAILED: The email addresses did not match. Run Solidus again and enter matching email addresses.")

        strEmailAddress = strEmailAddress.strip()
        SolidusConfigFile.writeSolidusConfigFile(strOriginGuid, strEmailAddress)
        
        locManager = LocationsManager(True)
        locManager.install()

        return strOriginGuid, strEmailAddress

    except Exception as err:
        SolidusErrorLog.logError(str(err), "installSolidus")
        #Delete the config file so we have to run the install routine again
        #!TFinish 1.0 - Add more robust error handling if deletion fails
        SolidusConfigFile.deleteSolidusConfigFile()
        sys.exit("INSTALL FAILED: Please email the SolidusError.log file to EpicFail@SolidusSecurity.com for troubleshooting help.")
            
def runSolidus():

    try:
        
        strOriginGuid, strEmailAddress = SolidusConfigFile.getSolidusOriginGuidAndRegisteredEmailAddress()

        if (strEmailAddress is None):
            strOriginGuid, strEmailAddress = installSolidus()
        else:
            locManager = LocationsManager(False)
            locManager.evaluateAllLocations()
            
        SolidusXMLLog.writeOriginInfoEvent(strEmailAddress)

        SolidusXMLLog.reportAllEvents(strOriginGuid)

    except SystemExit as err:
        print (str(err))
        raise
    
    except LocationsManagerError:
        SolidusErrorLog.logError("LocationsManager Failure", "runSolidus")  
        
    except Exception as err:
        SolidusErrorLog.logError(str(err), "runSolidus")  


runSolidus()
        
