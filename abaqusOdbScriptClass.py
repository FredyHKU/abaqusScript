# -*- coding:utf-8 -*-
"""
By fredyhku
Create - 20211001
abaqus scripts in python 2.7
only run in "abaqus python" env
class and functions for odb file operation
"""

import odbAccess
import json
import time
import locale

# ======================================================================\
# available functions
# log dict for information
def writeLog(msgKey="warn_200", withTime=True, info=""):
    msgDict = {
        "msg_000": "Abaqus python script eve.py",
        "msg_001": "Begin configure with command line options",
        "msg_002": "Load odb file",
        "msg_003": "Load odb file success - "+info,
        "msg_004": "Validate step names and node sets",
        "msg_005": "Begin get "+info+" data",
        "msg_006": "End get "+info+" data",
        "msg_007": "Save to "+info,
        "msg_008": "Abaqus python script COMPLETED",
        "msg_009": "Abaqus python script TERMINATED",
        "error_100": "Error: no command line option is given",
        "error_101": "Error: "+info+" is not a valid command line option",
        "error_102": "Error: "+info+" is not a valid argument for -t",
        "error_103": "Error: odb file is not specified",
        "error_104": "Error: field/history output is not specified",
        "error_110": "Error: open odb file failed\n"+info,
        "error_111": "Error: no valid step is specified",
        "error_112": "Error: no valid node set is specified",
        "error_130": "Error: no output data is extracted",
        "warn_200": "Warning: message key is not specified, test message",
        "warn_210": "Warning: invalid step "+info+" is ignored",
        "warn_211": "Warning: invalid node set "+info+" is ignored",
        "warn_240": "Warning: output filename not specified",
        "warn_241": "Warning: output file is not generated"
    }
    locale.setlocale(locale.LC_TIME, "en_US")
    timeMarker = time.strftime("%m/%d/%Y %I:%M:%S %p", time.localtime())
    if withTime:
        print timeMarker
    print msgDict[msgKey]
    return msgDict[msgKey]

# ======================================================================\
# local functions
# dictionary of command line options
def _commandLineOption(var):
    optionDict = {
        "-p": "path",                   # ODB file path is specified by the -p parameter in command line
        "-o": "odb",                    # ODB file name is specified by the -o parameter in command line
        "-t": "type",                   # Output type is specified by the -t parameter in command line
        "-s": "step",                   # Step(s) is specified by the -s parameter in command line
        "-n": "nodeSet",                # Node set(s) is specified by the -n parameter in command line
        "-f": "fileName",               # output file name (.json) is specified by the -f parameter in command line
        "-h": "help"                    # -h: show valid command line option
    }
    return optionDict.get(var,"error")  # return "error" for invalid command line option

# help of command line options
def _commandLineHelp(error=1):
    print "Command line options:"
    print " -p <odbfile path>\n -o <odb name>\n -t <field/history>\n -s <step name>\n -n <nodeset name>\n -f <output file name>\n -h <show help menu>"
    return error


# ======================================================================\
# !!! important class !!!
# the Class for reading odb file with abaqus python
class odbReader(object):
# ===================================\
    # Initialization
    def __init__(self,argList=None):
        self.option = {
            "path": ".",                        # default - working directory
            "odb": "",
            "dir": "",
            "type": "",
            "step": [],
            "nodeSet": [],
            "config": False,
            "fileName": ""
        }
        self.output = {}
        self.stepList = []
        self.nodeSetList = []
        self.odb = None
        self.error = 0
        # force configure with command line options
        self.error = self.config(argList)

# ===================================\
    # odbReader
    def __str__(self):
        return self.option

# ===================================\
    # Get arguments from command line
    def config(self, argList=None):
        # when there is an error
        if self.error:
            return 1
        # begin configure
        writeLog(msgKey="msg_001", withTime=True)
        # default - display help file
        if argList is None:
            argList = ["-h"]
        # skip the first argument, if it is *.py
        if argList[0][:-3] == ".py":
            skip = 1
        else:
            skip = 0
        # extract options
        readArgName = []
        for i in range(skip,len(argList)):
            if argList[i][0] == "-":               # command line option
                readArgName = _commandLineOption(argList[i])
                if readArgName == "error":
                    writeLog(msgKey="error_101", withTime=True, info=argList[i])
                    return _commandLineHelp(1)
                if readArgName == "help":
                    return _commandLineHelp(0)
            else:                                   # arguments
                if readArgName == "path":               # read path
                    self.option["path"] = argList[i]
                elif readArgName == "odb":              # read odb filename
                    name = argList[i]
                    if name[-4:] == ".odb":                 # add .odb extension if needed
                        self.option["odb"] = name
                    else:
                        self.option["odb"] = name + ".odb"
                elif readArgName == "type":             # read output type
                    outputType = argList[i]
                    if outputType not in ["field","history"]:   # check validation
                        writeLog(msgKey="error_102", withTime=True, info=outputType)
                        return _commandLineHelp(1)
                    else:
                        self.option["type"] = outputType
                elif readArgName == "step":
                    self.option["step"].append(argList[i])
                elif readArgName == "nodeSet":
                    self.option["nodeSet"].append(argList[i])
                elif readArgName == "fileName":
                    fName = argList[i]
                    if fName[-5:] == ".json":                 # add .json extension if needed
                        self.option["fileName"] = fName
                    else:
                        self.option["fileName"] = fName + ".json"
        if len(self.option["odb"]) == 0:
            writeLog(msgKey="error_103", withTime=True)
            return _commandLineHelp(1)
        else:
            self.option["dir"] = self.option["path"] + "\\" +  self.option["odb"]
        if len(self.option["type"]) == 0:
            writeLog(msgKey="error_104", withTime=True)
            return _commandLineHelp(1)
        self.option["config"] = True
        return 0

# ===================================\
    # Validate odb file and its objects
    def loadOdb(self):
        # when there is an error or no error but not configured - command line option help
        if self.error or not self.option["config"]:
            return 1
        # load odb file
        writeLog(msgKey="msg_002", withTime=True)
        try:
            odb = odbAccess.openOdb(self.option["dir"], readOnly=True)
        except Exception as odbErr:
            writeLog(msgKey="error_110", withTime=True, info=str(odbErr.message))
            return 1
        # load odb file success
        writeLog(msgKey="msg_003", withTime=True, info=self.option["odb"])
        # check steps and sort them
        writeLog(msgKey="msg_004", withTime=True)
        stepList = []
        for stepName in self.option["step"]:
            if stepName in odb.steps.keys():
                stepList.append((odb.steps.keys().index(stepName),stepName))
            else:
                writeLog(msgKey="warn_210", withTime=True, info=stepName)
        if len(stepList) == 0:
            writeLog(msgKey="error_111", withTime=True)
            odb.close()
            return 1
        else:
            stepList.sort(key=lambda x:x[0])
            self.stepList = stepList
        # check nodeSets
        nodeSetList = []
        for nodeSetName in self.option["nodeSet"]:
            if nodeSetName in odb.rootAssembly.nodeSets.keys():
                nodeSetList.append(nodeSetName)
            else:
                writeLog(msgKey="warn_211", withTime=True, info=nodeSetName)
        if len(nodeSetList) == 0:
            writeLog(msgKey="error_112", withTime=True)
            odb.close()
            return 1
        else:
            self.nodeSetList = nodeSetList
        # successfully open odb, return odb object
        self.odb = odb
        return 0

# ===================================\
    # history output data
    # return: history output data in dict
    #  error: {}
    def getHist(self):
        # whether odb file is loaded
        if self.odb is None:
            # load the odb file
            self.error = self.loadOdb()
        # when there is an error
        if self.error:
            return {}
        # after checking, continue with data extraction
        writeLog(msgKey="msg_005", withTime=True,info="history output")
        histOutputOfNodeSet = {}
        # for each nodeSet
        for nodeSetName in self.nodeSetList:
            odbMeshObjTemp = self.odb.rootAssembly.nodeSets[nodeSetName].nodes
            histOutputOfRegion = {}
            for i in range(0,len(odbMeshObjTemp)):
                for j in range(0,len(odbMeshObjTemp[i])):
                    # get history region label name
                    histRegion = "Node " + odbMeshObjTemp[i][j].instanceName + '.' + str(odbMeshObjTemp[i][j].label)
                    # export .historyOutputs as dict form: {step: historyOutputs}
                    historyOutputsTemp = historyOutputsDict()
                    for stepTuple in self.stepList:
                        step = stepTuple[1]
                        if histRegion in self.odb.steps[step].historyRegions.keys():
                            historyOutputsTemp.combineKeys(
                                self.__histOutputsObj2dict(
                                    self.odb.steps[step].historyRegions[histRegion].historyOutputs,step
                                )
                            )
                    # update history region level dict - {histRegion: histOutputTemp}
                    histOutputOfRegion.update({histRegion: historyOutputsTemp.dict})
            # update node set level dict - {nodeSetName: histOutputOfRegion}
            histOutputOfNodeSet.update({nodeSetName: histOutputOfRegion})
        self.odb.close()
        writeLog(msgKey="msg_006", withTime=True, info="history output")
        return histOutputOfNodeSet

# ===================================\
    # history output object to dict, local function
    def __histOutputsObj2dict(self, histObj,step):
        histOutputDict = {}
        for key in histObj.keys():
            histOutputDict.update({key: {step: histObj[key].data}})
        return histOutputDict

# ===================================\
    # overall output function
    # read data and save to json file
    # return: 0
    #  error: 1
    def exportData(self):
        # whether odb file is loaded
        if self.odb is None:
            # load the odb file
            self.error = self.loadOdb()
        # when there is an error
        if self.error:
            return 1
        # history / field output - call different functions
        if self.option["type"] == "history":
            self.output = self.getHist()
        else:
            print "Error: field output function is not completed"
            self.output = {}
        # check error code again
        if len(self.output) == 0:
            writeLog(msgKey="error_130", withTime=True)
            return 1
        else:
            # when there is no error
            # output to file
            self.write2json()
        return 0

# ===================================\
    # write data to .json
    def write2json(self):
        if len(self.option["fileName"]) == 0:
            writeLog(msgKey="warn_240", withTime=True)
            writeLog(msgKey="warn_241", withTime=False)
            return 1
        else:
            writeLog(msgKey="msg_007", withTime=True, info=self.option["fileName"])
            with open(self.option["fileName"], "w") as fp:
                json.dump({
                    "stepList": self.stepList,
                    "nodeSetList": self.nodeSetList,
                    "output": self.output
                }, fp, indent=1)
            return 0


# ======================================================================\
# local class
# class for history output: combine same keys in different steps
class historyOutputsDict(object):
# ===================================\
    # Initialization
    def __init__(self, initValue = None):
        if initValue is None:
            self.dict = {}
        else:
            self.dict = initValue

# ===================================\
    # historyOutputsDict
    def __repr__(self):
        return self.dict

# ===================================\
    # !!! Important !!!
    # example:
    # {'A1': {Step1: ((0,0),(0.1,1))}}
    # {'A1': {Step2: ((0,0),(0.1,2))}}
    # combineKeys:
    # {'A1': {Step1: ((0,0),(0.1,1)), Step2: ((0,0),(0.1,2))}}
    def combineKeys(self, newDict = None):
        if newDict is None:
            return self.dict
        elif len(self.dict) == 0:
            self.dict = newDict
        else:
            for key in newDict.keys():
                if key in self.dict.keys():
                    self.dict[key].update(newDict[key])
                else:
                    self.dict.update(newDict)
        return self.dict

'''
    def _upgrade(self):
        oldOdb = self.option["dir"]
        try:
            if odbAccess.isUpgradeRequiredForOdb(upgradeRequiredOdbPath=oldOdb):
                odbAccess.upgradeOdb(existingOdbPath=self.option["dir"], upgradedOdbPath=newOdb)
        except Exception as e:
            print e.message
            return 1
'''
