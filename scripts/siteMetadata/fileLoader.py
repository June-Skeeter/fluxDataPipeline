# Script to support parallelization of file loading
from scripts.submodules.fileParser import parseCSI,parseCSV

fileParsers = {
    'TOB3':parseCSI.TOB3,
    'TOA5':parseCSI.TOA5,
    'MixedArray':parseCSI.MixedArray,
    'HOBOcsv':parseCSV.HOBOcsv
}

def fileReader(fileName,fileFormat,kwargs):
    return(fileParsers[fileFormat](kwargs).read(fileName))

def fileLoader(fileName,backEnd,fileFormat,kwargs):
    df = fileParsers[fileFormat](kwargs).read(fileName)
    outcome = backEnd.loadDataFrame(df)
    return(outcome)