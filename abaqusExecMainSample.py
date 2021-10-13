# This is a sample Python script for class abaMultiExec

from abaqusExecClass import abaqusMultiExec as abEx

if __name__ == '__main__':
    adam = abEx(task="Demo", nRuns=9, nProc=32)
    err = adam.exec(execMode="para", NPara=4)
    adam.showRecords()
    print(adam.acq("index"))
    exit(err)

    # exit(abEx(3).indvExec(True))
