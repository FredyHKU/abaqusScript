# -*- coding:utf-8 -*-
"""
By fredyhku
Create - 20211008
testCase main function
"""

from caseGenerator import whiteNoiseFiltered as wnf
from caseGenerator import save2Json
from caseGenerator import checkConsist as consist
from abaqusInpModify import *
from abaqusExecClass import abaqusMultiExec as abEx
import sys
import os
import time

if __name__ == "__main__":

    # =====================================================/
    # set inp base file configure file and case file
    numOfCase = 20
    basePath = ".\\"
    inpBaseName = "rndWn+SinCableF_100s"
    # case folder
    caseFolder = time.strftime("%Y-%m-%d_%H.%M.%S", time.localtime()) + "_" + inpBaseName
    casePath = ".\\" + caseFolder
    inpPath = casePath + "\\InpFile"
    odbPath = casePath + "\\OdbFile"
    resultPath = casePath + "\\ResultJson"
    # configure and case json file
    configJsonDir = casePath + "\\config.json"
    caseJsonDir = casePath + "\\case.json"
    # config.json
    configData = {
        "wn1": [
            {
                "title": "*Amplitude, name=Lp10_WhiteNoise1_100s_pw1_fs1k",
                "parent": [],
                "type": "assign",
                "columnNumber": 7
            }
        ],
        "wn2": [
            {
                "title": "*Amplitude, name=Lp10_WhiteNoise2_100s_pw1_fs1k",
                "parent": [],
                "type": "assign",
                "columnNumber": 7
            }
        ]
    }
    # case.json
    caseData = []
    for i in range(0, numOfCase):
        wn1List = wnf(
                fs=1000, duration=100, power=1, lowPassConfig=[3, 50]
            ).flatten().tolist()
        wn2List = wnf(
                fs=1000, duration=100, power=1, lowPassConfig=[3, 50]
            ).flatten().tolist()
        caseData.append({
            "wn1": [str(format(wn1List[i], '.11g')) for i in range(0, len(wn1List))],
            "wn2": [str(format(wn2List[i], '.11g')) for i in range(0, len(wn2List))]
        })

    # =====================================================/
    # create path and save config.json & case.json
    os.makedirs(casePath)
    os.makedirs(inpPath)
    os.makedirs(odbPath)
    os.makedirs(resultPath)
    if consist(configData, caseData):
        save2Json(configJsonDir, configData)
        save2Json(caseJsonDir, caseData)

    # =====================================================/
    # modify and generate batch inp file
    if not inpBaseName[-4:] == ".inp":
        inpBaseName = inpBaseName+".inp"
    abaInpMd = abaqusInpModify(basePath+inpBaseName)
    abaInpMd.importConfig(configJsonDir)
    abaInpMd.importCase(caseJsonDir)
    abaInpMd.exportCase(inpPath, inpBaseName)

    # =====================================================/
    # configure adam.bat and eve.bat
    jobName = inpBaseName[:-4]
    with open("adam.bat", "w") as fp:
        fp.writelines("@echo off\n")
        fp.writelines("cd " + odbPath + "\n")
        fp.writelines("abaqus job=" + jobName + "%1 input=" + sys.path[0] + "\\" + inpPath + "\\" +
                      jobName + "%1.inp int ask_delete=OFF\n")
        fp.close()
    with open("eve.bat", "w") as fp:
        fp.writelines("@echo off\n")
        fp.writelines("abaqus python abaqusOdbScript.py -p " + odbPath + " -o " + jobName + "%1.odb " +
                      "-t history -n SENSOR1 SENSOR2 SENSOR3 -s TimeVaryCableForce " +
                      "-f " + resultPath + "\\" + jobName + "%1.json")
        fp.close()
    print("adam.bat and eve.bat are configured")

    # =====================================================/
    # abaqus multiExecution
    # JOB
    JOB = abEx(task="JOB", nRuns=numOfCase, nProc=4, logPath=caseFolder)
    errJOB = JOB.exec(execMode="para", NPara=4)
    JOB.showRecords()

    # =====================================================/
    # abaqus multiExecution
    # ODBScript
    ODBScript = abEx(task="ODBScript", nRuns=numOfCase, nProc=1, logPath=caseFolder)
    errODBScript = ODBScript.exec(execMode="indv")
    ODBScript.showRecords()
