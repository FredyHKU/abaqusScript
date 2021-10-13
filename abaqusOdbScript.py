# -*- coding:utf-8 -*-
"""
By fredyhku
Create - 20211005
abaqus scripts in python 2.7
only run in "abaqus python" env
main for odbScriptClass.py
"""
import sys
from abaqusOdbScriptClass import odbReader
from abaqusOdbScriptClass import writeLog

# ===================================\
# Main - abaqus python script
if __name__ == '__main__':
    # print welcome message
    writeLog(msgKey="msg_000", withTime=False)
    # run odbReader
    errorCode = odbReader(sys.argv).exportData()
    # print complete message if success
    # print terminate message if failure
    if not errorCode:
        writeLog(msgKey="msg_008", withTime=False)
    else:
        writeLog(msgKey="msg_009", withTime=False)
    exit(errorCode)
