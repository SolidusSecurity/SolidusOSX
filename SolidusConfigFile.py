import SolidusErrorLog

import os

#!TFinish 1.0 - Move this into a helper module and error handle
strApplicationPath = os.path.dirname(os.path.realpath(__file__)) + "/"
SOLIDUS_CONFIG_FILE_NAME = "Solidus.config"
SOLIDUS_CONFIG_FILE = strApplicationPath + SOLIDUS_CONFIG_FILE_NAME

class SolidusConfigFileError(Exception):
    pass

def writeSolidusConfigFile(strOriginGuidIn, strEmailAddressIn):
    try:
        outFile = open(SOLIDUS_CONFIG_FILE, "w")
        #!TFinish 1.0 - Tie this to agent version number properly
        outFile.write("Solidus Config File Version .1\n")
        outFile.write(strOriginGuidIn + "\n")
        outFile.write(strEmailAddressIn + "\n")
        outFile.close()
        
    except Exception as err:
        SolidusErrorLog.logError(str(err), "writeSolidusConfigFile")
        raise SolidusConfigFileError("Write Failed: " + str(err))
                         
def getSolidusOriginGuidAndRegisteredEmailAddress():

    try:        
        inFile = open(SOLIDUS_CONFIG_FILE, "r")

        #Ignore the version header at this time
        strFileVersionHeader = inFile.readline()

        strOriginGuid = inFile.readline().rstrip("\n")        

        strEmailAddress = inFile.readline().rstrip("\n")

        #This is expected if the file doesn't exist
        if (len(strEmailAddress) == 0):
            raise SolidusConfigFileError("Could not read in config settings")
            
        return strOriginGuid, strEmailAddress
                         
    #We need to reinstall if the config file does not exist or does not match what we expect
    except Exception as err:
        #Log an error if the file existed but the config file read in failed (missing file expected at times)
        try:
            if (os.path.exists(SOLIDUS_CONFIG_FILE)):
                SolidusErrorLog.logError(str(err), "getSolidusOriginGuidAndRegisteredEmailAddress")
                
        #Ignore if any error is encountered since this is just for logging
        except:
            pass
        
        return None, None

#Do not throw errors
def deleteSolidusConfigFile():
    try:
        if (os.path.exists(SOLIDUS_CONFIG_FILE)):
            os.remove(SOLIDUS_CONFIG_FILE)
    except:
        SolidusErrorLog.logError(str(err), "deleteSolidusConfigFile")
