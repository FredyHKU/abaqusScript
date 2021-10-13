# -*- coding:utf-8 -*-
"""
By fredyhku
Create - 20210923
Execute abaqus job/odbScript via bat file
"""

from pandas import DataFrame
import math
import multiprocessing as mp
import warnings
import os


# Define bat name dict
def _batName(var):
    batNameDict = {
        "JOB": "adam.bat",
        "ODBScript": "eve.bat",
        "DEMO": "welcome.bat"
    }
    # if type(var) == "list":
    #     return [batNameDict.get(var[i], "welcome.bat") for i in var]
    # else:
    #     return batNameDict.get(var, "welcome.bat")
    return batNameDict.get(var, "welcome.bat")


# execute abaqus via bat - local basic function
# input:    index       int     index in job name / inp. name / odb name / json name
#           printFlg    bool    print use
# return:   -           dict    keys: index, flag, logs
def _batExec(task="Demo", index=0, printFlg=False):
    import subprocess
    print("Abaqus " + task + " execution STARTED: No." + str(index))
    # call abaqus via *.bat
    flag = True
    logs = subprocess.Popen(_batName(task)+" "+str(index),
                            shell=False,
                            stdout=subprocess.PIPE,
                            universal_newlines=True
                            ).stdout.read()
    # check whether the analysis is successful
    if "COMPLETED" not in logs:
        flag = False
        print("Abaqus "+task+" execution failed: No."+str(index))
        print("Check "+_batName(task)+".log for error messages!")
    else:
        print("Abaqus "+task+" execution COMPLETED: No."+str(index))
    # print (for debug/single call)
    if printFlg:
        print(logs)
    # return dict type records
    return {"index": index,
            "flag": flag,
            "logs": logs}


# handle for parallel pool
def _batExecHandle(args):
    return _batExec(*args)


# class for abaqus execution
class abaqusMultiExec(object):

    # initialize
    def __init__(self, task="DEMO", nRuns=1, nProc=60, logPath="."):
        # default record database
        recordDefault = {"index": [],
                         "flag": [],
                         "logs": []}
        self.recordKeys = recordDefault.keys()
        # _recordsDf is a dataframe from pandas, local variable
        self._recordsDf = DataFrame(recordDefault, columns=self.recordKeys)
        # task type
        self.task = task
        # index for execution (case No.) | default all cases
        self.idxExec = [n for n in range(nRuns)]
        # parameters for parallel execution
        # number of processors | default maximum cpus
        self.NProc = min(mp.cpu_count(), nProc, 60)
        # number of parallel execution | default 2
        self.NPara = 2
        # log file path
        if os.path.exists(logPath):
            self.logPath = logPath
        else:
            print("Warning: logPath specified does not exist!")
            print("default logPath .\\ is used")
            self.logPath = "."

    # when use obj name directly - export all records as dict
    def __str__(self):
        return self._recordsDf.to_dict("list")

    # !!! IMPORTANT !!!
    # execution - user attributes
    # input     execMode    str         "para", "indv", default - "para"
    #           idxExec     list        case index to be executed, default - see __init__
    #           NProc       int         number of processors for parallel execution, default - see __init__
    #           NPara       int         number of parallel tasks, default - see __init__
    #           printLogs   bool        print log file, default - 1
    # output    err         bool        all complete - 0, else 1
    def exec(self,
             execMode: str = "para",
             idxExec: list = None,
             NProc: int = None,
             NPara: int = None,
             printLogs: bool = True):
        # input arguments
        if idxExec is not None:
            self.idxExec = idxExec
        if NProc is not None:
            self.NProc = NProc
        if NPara is not None:
            self.NPara = NPara
        # execute tasks
        if execMode == "para":
            err = self._paraExec(printLogs)
        elif execMode == "indv":
            err = self._indvExec(printLogs)
        else:
            err = 1
            warnings.warn("Unexpected execution mode specified!", UserWarning)
        return err

    # acquire one or several keys - user attributes
    # input     acqKeys     str/list    key names for data acquire, default - all keys (keys name see __init__)
    # output    ans         list/dict   list - one key / dict - more than one key
    def acq(self, acqKeys=None):
        # default acquired keys - self.recordKeys
        # modify type to list
        if acqKeys is None:
            acqKeys = self.recordKeys
        else:
            if not type(acqKeys) == "list":
                acqKeys = [acqKeys]
        # check valid keys
        validKeys = [key for key in acqKeys if key in self.recordKeys]
        if not validKeys == acqKeys:
            warnings.warn("Invalid keys observed in abaMultiExec.acq!", UserWarning)
        # output list/dict with valid keys
        if len(validKeys) == 0:
            ans = []
        else:
            if len(validKeys) == 1:
                ans = self._recordsDf.to_dict("list")[validKeys[0]]
            else:
                ans = {key: self._recordsDf.to_dict("list")[key] for key in validKeys}

        return ans

    # print all records to screen - user attributes
    def showRecords(self):
        print(self._recordsDf)
        return 0

    # -------- local functions -------- #

    # print abaqus logs to .log file
    def printLogs(self):
        logFile = open(self.logPath + "\\" + _batName(self.task)+".log", "w")
        for logs in self.acq("logs"):
            print(logs, file=logFile)
            print("---------------------------------------", file=logFile)
        logFile.close()

        return 0

    # parallel execution - local basic function
    # input     printFlg    bool        print log file, default - 1
    # output    err         bool        all complete - 0, else 1
    def _paraExec(self, printFlg=True):
        # # define function handle for para
        # def _batExecHandle(x=0):
        #     return _batExec(task=self.task, index=x, printFlg=False)
        # number of executions in total
        NRuns = len(self.idxExec)
        # number of parallel execution processes
        NPara = self.NPara
        # start parallel pool
        pool = mp.Pool(processes=self.NProc)
        # non-para loop
        for i in range(math.ceil(NRuns / NPara)):
            # left right end index of parallel loops
            leftIdx = i * NPara
            rightIdx = min(NRuns, (i + 1) * NPara)
            # start parallel execution
            paraArgs = [(self.task, self.idxExec[idx], True) for idx in range(leftIdx, rightIdx)]
            tempOuts = pool.map(_batExecHandle, paraArgs)
            # append outputs to _recordsDf
            self._recordsDf = self._recordsDf.append(
                DataFrame(tempOuts, columns=tempOuts[0].keys()), ignore_index=True)
            # End for
        pool.close()
        # sort records based on key "index"
        self._recordsDf = self._recordsDf.sort_values(
            by="index", axis=0, ascending=True, ignore_index=True)
        # print to log
        if printFlg:
            self.printLogs()

        return int(False in self.acq("flag"))

    # individual execution - local basic function
    # input     printFlg    bool        print log file, default - 1
    # output    err         bool        all complete - 0, else 1
    def _indvExec(self, printFlg=True):
        # non-para loop
        for index in self.idxExec:
            # one single execution
            # temp data storage
            tempOuts = _batExec(self.task, index, True)
            # append outputs to _recordsDf
            self._recordsDf = self._recordsDf.append(
                DataFrame([tempOuts], columns=tempOuts.keys()), ignore_index=True)
            # End for
        # sort records based on key "index"
        self._recordsDf = self._recordsDf.sort_values(
            by="index", axis=0, ascending=True, ignore_index=True)
        # print to log
        if printFlg:
            self.printLogs()

        return int(False in self.acq("flag"))
