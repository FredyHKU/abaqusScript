# -*- coding: utf-8 -*-
"""
Created on Thu Jan  7 10:14:20 2021

@author: jiang
modified by Fred 2021/10/06
"""
import json

TYPE_DIC = {
    'string': str,
    'int': int,
    'float': float
    }

FORMAT_ASSIGN = 'assign'
FORMAT_RATIO = 'ratio'


def modifyNumber(string, formatString):
    if formatString.startswith('%'):
        number = float(formatString[3:])
        decimalDigits = int(formatString[1])
        operationType = formatString[2]
        if operationType == '*':
            return str(round(float(string) * number, decimalDigits))
        elif operationType == '+':
            return str(round(float(string) + number, decimalDigits))
        else:
            raise RuntimeError(f'FormatString wrong {formatString}')
    else:
        return formatString
    
    
class Format(object):
    def __init__(self, index, formatDic, dataRow):
        self.index = index
        self.formatDic = formatDic
        self.dataRow = dataRow

    def handleList(self, inputList):
        columnnumber = self.formatDic.get("columnNumber", 0)
        if self.formatDic['type'] == 'assign':
            self.dataRow.formOutput(inputList, columnnumber)
        elif self.formatDic['type'] == 'modify':
            outputList = self.dataRow.variableList.copy()
            for index, position in enumerate(self.formatDic['position']):
                print(position, index, outputList)
                string = modifyNumber(outputList[position], inputList[index])
                outputList[position] = string
            self.dataRow.formOutput(outputList, columnnumber)


class DataRow(object):
    def __init__(self, index, string):
        self.index = index
        self.string = string
        self.outputString = string
        self.variableList = []
        self.parseString()
    
    def parseString(self):
        string = self.string.replace('\n', ',')
        self.variableList = string.split(',')
    
    def reset(self):
        self.outputString = self.string
    
    def formOutput(self, outputList, columnNumber=0):
        l = outputList.copy()
        length = max([len(x) for x in l]) + 1
        l = [x.rjust(length) for x in l]
        length = max(length, 5)
        if not columnNumber:
            columnNumber = 120 // length
        start = 0
        string = ''
        output = []
        for x in l:
            # print(f'here is {x} , {string}')
            if start == columnNumber:
                string = string + ',' + x
                output.append(string)
                start = 0
                string = ''
            else:
                start += 1
                string = string + ',' + x
        if string:
            output.append(string)
        self.outputString = '\n'.join([x.lstrip(',') for x in output])
        # print(outputList, output)
        
    
class abaqusInpModify(object):
    def __init__(self, path):
        self.inpList = []
        self.config = None
        self.rawRowDic = {}
        self.variableDic = {}
        self.importINP(path)
        
    def importConfig(self, path):
        try:
            with open(path, 'r') as fp:
                self.config = json.load(fp)
        except:
            print('Config file error. Can\'t find', path)
                 
        for x in self.config:
            formatList = []
            self.variableDic[x] = formatList
            for singleDic in self.config[x]:
                keyString = singleDic['title']
                parent = singleDic.get('parent', [])
                if parent:
                    for y in parent:
                        parentIndex = self.searchForParent(y)
                        index = self.searchForKey(keyString, parentIndex)
                        if index not in self.rawRowDic:                     
                            self.rawRowDic[index + 1] = DataRow(index + 1, self.inpList[index + 1])
                        formatList.append(Format(index, singleDic, self.rawRowDic[index + 1]))
                else:
                    index = self.searchForKey(keyString, 0)
                    if index not in self.rawRowDic:                     
                        self.rawRowDic[index + 1] = DataRow(index + 1, self.inpList[index + 1])
                    formatList.append(Format(index, singleDic, self.rawRowDic[index + 1]))
            
    def importINP(self, path):
        try:
            with open(path, 'r') as fp:
                inpList = fp.readlines()
        except:
            print('Inp file error. Can\'t find', path)
            return 1
        l = []
        startPosition = -1
        endPosition = -1
        for index, x in enumerate(inpList):
            if x.startswith("*"):
                if startPosition != -1:
                    l.append(''.join(inpList[startPosition: endPosition]))
                    startPosition = -1
                    endPosition = -1
                l.append(x)
            else:
                if startPosition == -1:
                    startPosition = index
                    endPosition = index + 1
                else:
                    endPosition += 1
        self.inpList = [x.rstrip('\n') for x in l]
        return 0
    
    def importCase(self, path):
        try:
            with open(path, 'r') as fp:
                self.caseList = json.load(fp)
        except:
            print(f'Case file error. Can\'t find {path}')
            
    def exportCase(self, *args):
        for index, caseDic in enumerate(self.caseList):
            # try:
            for key in caseDic:
                formatList = self.variableDic[key]
                for formatInstance in formatList:
                    formatInstance.handleList(caseDic[key])
            # except Exception as e:
            #     print(e)
            #     print(f'Case {index} is wrong.')
            self.exportFile(*args, index)
            for x in self.rawRowDic.values():
                x.reset()

    def exportFile(self, folderName, jobName, index):
        if jobName[-4:] == ".inp":
            jobName = jobName[0:-4]
        with open(folderName + "\\" + jobName + str(index) + '.inp', 'w+') as fp:
            outputList = self.inpList.copy()
            for x in self.rawRowDic:
                outputList[x] = self.rawRowDic[x].outputString
            fp.writelines([x+'\n' for x in outputList])

    def searchForParent(self, parentString):
        if parentString == '':
            return 0
        try:
            index = self.inpList.index(parentString)
            return index
        except ValueError:
            print('Parent error. Can\'t find', parentString)
            raise RuntimeError('Parent Error')

    def searchForKey(self, keyString, start):
        try:
            index = self.inpList.index(keyString, start)
            return index
        except:
            print(f'title error. Can\'t find {keyString} start from {start}')
            raise RuntimeError('Title Error')


if __name__ == "__main__":
    inpPath = "testCase.inp"
    abaInpMd = abaqusInpModify(inpPath)

    configPath = "config.json"
    abaInpMd.importConfig(configPath)

    casePath = "case.json"
    abaInpMd.importCase(casePath)

    exportFolder = "InputFile"
    exportJobName = "testCase.inp"
    abaInpMd.exportCase(exportFolder, exportJobName)
