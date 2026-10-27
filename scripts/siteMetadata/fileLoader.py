# Script to support parallelization of file loading
import pandas as pd
from scripts.submodules.fileParser import parseCSI,parseCSV
from scripts.submodules.fluxCalculator.ecf32.ecf32Create import highFrequency,ghgTemplate

fileParsers = {
    'TOB3':parseCSI.TOB3,
    'TOA5':parseCSI.TOA5,
    'MixedArray':parseCSI.MixedArray,
    'HOBOcsv':parseCSV.HOBOcsv
}

def fileReader(fileName,fileFormat,kwargs):
    return(fileParsers[fileFormat](kwargs).read(fileName))

def hfFileLoader(fileName,outputPath,siteID,fileID,fileFormat,metadataGroups,metadataTimeSeries,kwargs):
    df = fileParsers[fileFormat](kwargs).read(fileName)
    step = f"{metadataTimeSeries.index.diff().median().total_seconds()}s"
    start = df.index[0].floor(step)
    if start not in metadataTimeSeries.index or pd.isna(metadataTimeSeries[start]):
        return(False)
    record = metadataGroups.loc[metadataTimeSeries[start]]
    record = {key:record[key].fillna('').to_dict() for key in ghgTemplate.__annotations__}
    hf = highFrequency(outputPath=outputPath,siteID=siteID,fileID=fileID,typeEnforce=True,**record).loadDataFrame(df)
    # outcome = highFrequency.loadDataFrame(df)
    return(True)