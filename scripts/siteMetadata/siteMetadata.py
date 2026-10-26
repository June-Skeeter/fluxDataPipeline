import os
import numpy as np
import pandas as pd
from fnmatch import fnmatch
from datetime import datetime, timezone
from dataclasses import dataclass, field
from scripts.submodules.fileParser import parseCSI,parseCSV
from scripts.siteMetadata.instrumentation import hardwareModels
from scripts.submodules.Binary_Database.database import database
from scripts.submodules.helperFunctions.dataclassAddOns import dataclassFromYaml, classMethods
from scripts.submodules.helperFunctions.dictFunctions import dictFunctions
from scripts.submodules.fluxCalculator.ecf32.ecf32Create import highFrequency,ghgMetadataWriter

configurations = os.path.join(os.getcwd(),'configFiles')
site = dataclassFromYaml(os.path.join(configurations,'siteConfiguration.yml'),bases=(classMethods,dictFunctions))

fileParsers = {
    'TOB3':parseCSI.TOB3,
    'TOA5':parseCSI.TOA5,
    'MixedArray':parseCSI.MixedArray,
    'HOBOcsv':parseCSV.HOBOcsv
}

@dataclass(kw_only=True)
class siteConfiguration(site):
    saveTo: str = field(default=None,repr=False)
    validate: bool = field(default=False,repr=False)
    sourceFileInventory: dict = field(default_factory=dict,repr=False,init=False)

    def __post_init__(self):
        if hasattr(self,'__classmethod_flag__') and self.__classmethod_flag__['method'] == 'from_yaml':
            self.source = self.__classmethod_flag__['source']
            self.saveTo = os.path.split(self.__classmethod_flag__['fpath'])[0]
            fname= os.path.join(self.saveTo,f"{self.siteID}_instrumentHistory.csv")
            if not os.path.isfile(fname) or self.validate:
                self.validateMetadata()
            self.instrumentHistory = pd.read_csv(fname,index_col=[0],header=[0])
            fname= os.path.join(self.saveTo,f"{self.siteID}_ecInstrumentGroups.csv")
            self.ecInstrumentGroups = pd.read_csv(fname,index_col=[0],header=[0,1])
            fname = os.path.join(self.saveTo,'sourceFiles','.sourceFileInventory.json')
            self.sourceFileInventory = self.loadDict(fname)
        else:
            self.source = None
            if self.saveTo:
                self.validateMetadata()

    def saveSite(self):
        os.makedirs(self.saveTo,exist_ok=True)
        fname = os.path.join(self.saveTo,f"{self.siteID}_siteMetadata.yml")
        if not os.path.isfile(fname):
            print(f"Saving siteMetadata to: {fname}")
            self.saveDict(self.dcToDict(self),fname)
        elif self.source:
            self.saveDict(self.source,fname)
        fname = os.path.join(self.saveTo,f"{self.siteID}_instrumentHistory.csv")
        print(f"Saving instrumentHistory to: {fname}")
        self.instrumentHistory.to_csv(fname)
        fname = os.path.join(self.saveTo,f"{self.siteID}_ecInstrumentGroups.csv")
        print(f"Saving ecInstrumentGroups to: {fname}")
        self.ecInstrumentGroups.to_csv(fname)
        fname = os.path.join(self.saveTo,'sourceFiles','.sourceFileInventory.json')
        # if not os.path.isfile(fname):
        self.saveDict(self.sourceFileInventory,fname,indent=4)

    def validateMetadata(self):
        print(f"validating {self.siteID}_siteMetadata.yml")
        # if loaded from yaml, insert missing parameters, preserve flags
        if self.source:
            self.checkSiteParameters()
        self.checkInstruments()
        self.getInstrumentHistory()
        self.makeMetadataFiles()
        if self.saveTo:
            self.saveSite()

    def checkSiteParameters(self):
        for key in site.__annotations__.keys():
            value = getattr(self,key)
            if key.startswith('date'):
                if isinstance(value,str):
                    temp = datetime.fromisoformat(value)
                else:
                    print('Warning: wrap YAML timestamps with quotes to presever anchor tags; tags aer lost when parsing pure timestamp objects')
                    temp = value
                if temp.tzinfo is None:
                    exit(f"Error  in {self.__classmethod_flag__['fpath']}\n{key}: dates must specify UTC offset in yaml timestamp, e.g., +00:00, -06:00, etc.")
            if not isinstance(value, dict):
                if key not in self.source:
                    self.source[key] = value
                elif value != self.source[key]:
                    exit('Unexpected error in checkSiteParameters')                

    def checkInstruments(self):
        temp = self.instrumentation.copy()
        self.instrumentation = {}
        for kind,values in temp.items():
            self.instrumentation.setdefault(kind,{})
            if kind not in hardwareModels.keys():
                self.logError(f"Instrumentation kind = {kind} not yet supported, see/update {hardwareModels['path']}")
                
            for sourceID,model in values.items():
                modelName = model['modelName'].lower()
                if modelName not in hardwareModels[kind].keys():
                    self.logError(f"Instrumentation model = {modelName} of kind = {kind} not yet supported, see/update {hardwareModels['path']}")
                model = hardwareModels[kind][modelName](**model)
                if model.dateStart == '':
                    print(f"{model.ID} missing dateStart, defaulting to site-level value: {self.dateStart}")
                    model.dateStart = self.dateStart
                if model.dateStop == '':
                    print(f"{model.ID} missing dateStop, defaulting to site-level value: {self.dateStop}")
                    model.dateStop = self.dateStop
                if model.stationName == '':
                    print(f'Warning: witout statinoName, {model.ID} cannot be auto-linked to a datalogger, which may impact performance')
                self.instrumentation[kind][model.ID] = model
                if self.source:
                    for key,value in model.__dict__.items():
                        if key not in self.source['instrumentation'][kind][sourceID]:
                            self.source['instrumentation'][kind][sourceID][key] = value
        
    def getInstrumentHistory(self):
        self.instrumentHistory = pd.DataFrame()
        if len(self.instrumentation['biometSensors']):
            biometSensors = self.instrumentation['biometSensors']
            biometHistory = pd.concat([
                pd.Series(
                    data=True,
                    name=v.ID,
                    index=pd.date_range(
                        datetime.fromisoformat(v.dateStart).astimezone(timezone.utc),
                        datetime.fromisoformat(v.dateStop).astimezone(timezone.utc),
                        freq=f"1800s"),
                        )
                for k,v in biometSensors.items()
                ],axis=1,sort=True)
            biometInstrumentHistory = pd.Series('',index=biometHistory.index,name='biometSensors')
            for sen in biometHistory.columns:
                biometInstrumentHistory.loc[biometHistory[sen].notna()] += f"-{sen}"
            biometInstrumentHistory = biometInstrumentHistory.str.strip('-')
            self.instrumentHistory = pd.concat([biometInstrumentHistory])
        if len(self.instrumentation['ecSensors']):
            ecSensors = self.instrumentation['ecSensors']
            ecHistory = pd.concat([
                pd.Series(
                    data = True,
                    name=v.ID,
                    index=pd.date_range(
                        datetime.fromisoformat(v.dateStart).astimezone(timezone.utc),
                        datetime.fromisoformat(v.dateStop).astimezone(timezone.utc),
                        freq='1800s'),
                        )
                if hasattr(v,'referenceSonic') and v.referenceSonic else
                pd.Series(
                    data = False,
                    name=v.ID,
                    index=pd.date_range(
                        datetime.fromisoformat(v.dateStart).astimezone(timezone.utc),
                        datetime.fromisoformat(v.dateStop).astimezone(timezone.utc),
                        freq='1800s'),
                        )
                for k,v in ecSensors.items() 
            ],axis=1,sort=True)
            if ecHistory.sum(axis=1).max()>1:
                self.logError(f"Only one reference sonic allowed per-timestamp {ecHistory.loc[ecHistory.sum(axis=1)>1]}")
            # Select reference sonics and perform positional calculations based off this for all scalar systems
            ecInstrumentHistory = pd.Series('',index=ecHistory.index,name='ecSensors')
            for ref in ecHistory.columns[ecHistory.sum()>0]:
                refSonic = self.instrumentation['ecSensors'][ref]
                if refSonic.instrumentType == 'sonic_irga':
                    scalars = [ref]
                else:
                    scalars = []
                # Find all sensors referenced to the given sonic
                scalars += list(ecHistory.columns[ecHistory.loc[ecHistory[ref]==True].count()-ecHistory.loc[ecHistory[ref]==True].sum()>0])
                ecInstrumentHistory.loc[ecHistory[ref].notna()] = ref
                for scalar in scalars:
                    ecInstrumentHistory.loc[ecHistory[scalar].notna()] += f"-{scalar}"
                    # Convert x,y separation in northwardSeparation, eastwardSeparation using north offset
                    # geographicSeparation is method added to sonic instrumentals
                    x,y = self.instrumentation['ecSensors'][scalar].xSeparation,self.instrumentation['ecSensors'][scalar].ySeparation
                    self.instrumentation['ecSensors'][ref].geographicSeparation
                    north,east=self.instrumentation['ecSensors'][ref].geographicSeparation(x,y)
                    setattr(self.instrumentation['ecSensors'][scalar],'northwardSeparation',north)
                    setattr(self.instrumentation['ecSensors'][scalar],'eastwardSeparation',east)
            ecInstrumentHistory = ecInstrumentHistory.str.strip('-')
            self.instrumentHistory = pd.concat([self.instrumentHistory,ecInstrumentHistory],axis=1)
            
    def makeMetadataFiles(self):
        # Generate the template .metadata file for the group, to be filled with FileDescription at a later stage (in case different files for same configuration)
        ghgMetadata = ghgMetadataWriter()
        ghgMetadata.newFile(site_id=self.siteID,latitude=self.latitude,longitude=self.longitude,altitude=self.altitude)
        self.ecInstrumentGroups = []
        for groupID,groupDates in self.instrumentHistory[['ecSensors']].reset_index().groupby('ecSensors').agg(['min','max']).iterrows():
            ghgMetadata.setDates(
                start_date=groupDates['index']['min'].isoformat(),
                stop_date=groupDates['index']['max'].isoformat(),          
                )
            for i,instrument in enumerate(groupID.split('-')):
                instrument = self.instrumentation['ecSensors'][instrument]
                ghgMetadata.setInstrument(
                    ix=i+1,
                    id=instrument.ID,
                    model=instrument.modelName,
                    manufacturer=instrument.manufacturer,
                    height=instrument.Zm if 'sonic' in instrument.instrumentType else '',
                    north_offset=instrument.northOffset if 'sonic' in instrument.instrumentType else '',
                    northward_separation=instrument.northwardSeparation if hasattr(instrument,'northwardSeparation') else '',
                    eastward_separation=instrument.eastwardSeparation if hasattr(instrument,'eastwardSeparation') else '',
                    vertical_separation=instrument.verticalSeparation if hasattr(instrument,'verticalSeparation') else '',
                    tube_length=instrument.tubeLength if hasattr(instrument,'tubeLength') else '',
                    tube_diameter=instrument.tubeDiameter if hasattr(instrument,'tubeDiameter') else ''
                    )
            self.ecInstrumentGroups.append(pd.DataFrame(index=[groupID],data=ghgMetadata.asDictionary(flat=True)))
        self.ecInstrumentGroups = pd.concat(self.ecInstrumentGroups,sort=True)

    def findFiles(self,fileID,searchPath,fileNameMatch,fileNameExclude=''):
        if not fileNameMatch.startswith('*'):
            fileNameMatch = f"*{fileNameMatch}"
        self.sourceFileInventory.setdefault(fileID,{})
        newFiles = {
                    os.path.join(dir,file):None
                    for dir,_,files in os.walk(searchPath)
                    for file in files if (
                        fnmatch(os.path.join(dir,file),fileNameMatch) and 
                        not fnmatch(os.path.join(dir,file),fileNameExclude) and
                        os.path.join(dir,file) not in self.sourceFileInventory[fileID]
                    )
                }
        print(f"New files found: {len(newFiles)}")
        self.sourceFileInventory[fileID] = self.sourceFileInventory[fileID] | newFiles
        self.saveSite()

    def loadFiles(self,writeTo,fileID,fileFormat,kwargs={}):
        request_path = os.path.join(self.saveTo,'sourceFiles',f'{fileID}.yml')
        if os.path.isfile(request_path):
            request_kwargs = self.loadDict(request_path)
            if kwargs != {} and kwargs != request_kwargs:
                exit(f'Submitted kwargs do not match previous request.  Edit {fileID}.yml, or provide new fileID to ensure consistency.')
            else:
                kwargs = request_kwargs

        if writeTo.endswith('Database'):
            writer = database(databasePath=os.path.join(writeTo,'yyyy',self.siteID,fileID))
        elif writeTo.endswith('highFrequency'):
            writer = highFrequency(outputPath=os.path.join(writeTo,self.siteID,'yyyymm'),siteID=self.siteID,fileID=fileID,typeEnforce=True)
        for file in [file for file,md in self.sourceFileInventory[fileID].items() if md is None]:
            df = fileParsers[fileFormat](kwargs).read(file)
            if isinstance(writer,database) and np.nanmedian(df.index.diff().total_seconds().values)<1:
                exit('Error: database format fails at sub-second frequency.  Write to highFrequency instead')
            elif isinstance(writer,highFrequency) and np.nanmedian(df.index.diff().total_seconds().values)>writer.fileIntervalSeconds:
                exit('Error: highFrequency not preferred for low-frequency data.  Write to database instead')
            outcome = writer.loadDataFrame(df)
            if isinstance(outcome,str) and outcome.startswith('Warning'):
                print(outcome)
                breakpoint()
            self.sourceFileInventory[fileID][file] = outcome
        self.saveDict(kwargs,request_path)
        self.saveSite()    
        breakpoint()   
        # else:
        #     breakpoint() 
            
