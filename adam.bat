@echo off
cd .\2021-10-13_01.11.02\OdbFile
abaqus job=rndWn+SinCableF_100s%1 input=E:\01Research\12PythonProjects\abaqusScript\.\2021-10-13_01.11.02\InpFile\rndWn+SinCableF_100s%1.inp int ask_delete=OFF
