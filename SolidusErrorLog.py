import os

#!TFinish 1.0 - Move this into a helper module and error handle
strApplicationDirectory = os.path.dirname(os.path.realpath(__file__)) + "/"
SOLIDUS_ERROR_LOG_FILE_NAME = "SolidusError.log"
SOLIDUS_ERROR_LOG_FILE = strApplicationDirectory + SOLIDUS_ERROR_LOG_FILE_NAME

def openErrorLogFile(strModeIn):
    return open(SOLIDUS_ERROR_LOG_FILE, strModeIn)

def logError(strErrorTextIn, strFunctionNameIn):
    try:
        outFile = openErrorLogFile("a")
        outFile.write(strErrorTextIn + " occurred in " + strFunctionNameIn + "\n")
        outFile.close()
    #We have to ignore this if we cannot log it successfully
    except:
        pass

def logCodeMistakeError(strErrorTextIn, strFunctionNameIn):
    logError("CODE MISTAKE: " + strErrorTextIn, strFunctionNameIn)
