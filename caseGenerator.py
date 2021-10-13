# -*- coding:utf-8 -*-
"""
By fredyhku
Create - 20211008
Generate case.json
white noise
"""

import json
import numpy as np
from scipy import signal
import math
import matplotlib.pyplot as plt


# generate white noise function filtered
def whiteNoiseFiltered(fs=1000, duration=100, power=1, lowPassConfig=None):
    # generate time series and white noise
    tSeries = np.array([i for i in range(0, math.floor(fs*duration)+1)])/fs
    wnSeries = np.random.normal(scale=power, size=tSeries.shape)
    # lowPass filter if assigned
    if lowPassConfig is not None:
        b, a = signal.butter(*lowPassConfig, fs=fs)
        wnSeries_filter = signal.filtfilt(b, a, wnSeries)
        wnSeries = wnSeries_filter
    '''
    fig, ax = plt.subplots()
    ax.plot(tSeries, wnSeries)
    ax.set(xlabel='time (s)', ylabel='amplitudes',
           title='white noise generated')
    ax.grid()
    fig.savefig("white noise generated.png")
    plt.show()
    '''
    return np.stack((tSeries, wnSeries), axis=-1)


# input: [{"variable name": variable values,...}...]
def save2Json(jsonFile=None, dataOutput=None):
    if dataOutput is None or len(dataOutput) == 0:
        print("Error: no validate output data")
        return 1
    if not jsonFile[-4:] == "json":
        jsonFile = jsonFile+".json"
    with open(jsonFile, "w") as fp:
        json.dump(dataOutput, fp, indent=1)
        print(jsonFile[jsonFile.rfind("\\")+1:]+" has been generated")
    return 0


# check variables
def checkConsist(configData, caseData):
    if len(caseData) > 0 and not configData.keys() == caseData[0].keys():
        print("Error: variables in configure file and case file are not consistent")
        return False
    else:
        return True
    