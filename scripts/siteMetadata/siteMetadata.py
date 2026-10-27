import os
import uuid
import numpy as np
import pandas as pd
from fnmatch import fnmatch
from functools import partial
from datetime import datetime, timezone
from dataclasses import dataclass, field
from concurrent.futures import ProcessPoolExecutor
from scripts.siteMetadata.instrumentation import hardwareModels
from scripts.submodules.Binary_Database.database import database
from scripts.siteMetadata.fileLoader import hfFileLoader,fileReader
from scripts.submodules.helperFunctions.dataclassAddOns import dataclassFromYaml, classMethods
from scripts.submodules.helperFunctions.dictFunctions import dictFunctions
from scripts.submodules.fluxCalculator.ecf32.ecf32Create import ghgMetadataWriter

configurations = os.path.join(os.getcwd(),'configFiles')
site = dataclassFromYaml(os.path.join(configurations,'siteConfiguration.yml'),bases=(classMethods,dictFunctions))

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
            self.instrumentHistory = pd.read_csv(fname,index_col=[0],header=[0],parse_dates=[0])
            fname = os.path.join(self.saveTo,'sourceFiles',f'{self.siteID}_instrumentHistory.json')
            self.instrumentIndexMap = self.loadDict(fname)
            fname= os.path.join(self.saveTo,f"{self.siteID}_fluxInstrumentGroups.csv")
            self.fluxInstrumentGroups = pd.read_csv(fname,index_col=[0],header=[0,1])
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
        fname = os.path.join(self.saveTo,'sourceFiles',f'{self.siteID}_instrumentHistory.json')
        self.saveDict(self.instrumentIndexMap,fname,indent=4)
        fname = os.path.join(self.saveTo,f"{self.siteID}_fluxInstrumentGroups.csv")
        print(f"Saving fluxInstrumentGroups to: {fname}")
        self.fluxInstrumentGroups.to_csv(fname)
        fname = os.path.join(self.saveTo,'sourceFiles','.sourceFileInventory.json')
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
                exit(f"Instrumentation kind = {kind} not yet supported, update configFiles/instrumentation")
                
            for sourceID,model in values.items():
                modelName = model['modelName'].lower()
                if modelName not in hardwareModels[kind].keys():
                    exit(f"Instrumentation model = {modelName} of kind = {kind} not yet supported, update configFiles/instrumentation")
                model = hardwareModels[kind][modelName](**model)
                if model.dateStart == '':
                    print(f"{model.instrumentID} missing dateStart, defaulting to site-level value: {self.dateStart}")
                    model.dateStart = self.dateStart
                if model.dateStop == '':
                    print(f"{model.instrumentID} missing dateStop, defaulting to site-level value: {self.dateStop}")
                    model.dateStop = self.dateStop
                if model.stationName == '':
                    print(f'Warning: witout statinoName, {model.instrumentID} cannot be auto-linked to a datalogger, which may impact performance')
                self.instrumentation[kind][model.instrumentID] = model
                if self.source:
                    for key,value in model.__dict__.items():
                        if key not in self.source['instrumentation'][kind][sourceID]:
                            self.source['instrumentation'][kind][sourceID][key] = value
        
    def getInstrumentHistory(self):
        self.instrumentIndexMap = {'biomet':{},'flux':{}}
        self.instrumentHistory = pd.DataFrame()
        if len(self.instrumentation['biomet']):
            biomet = self.instrumentation['biomet']
            biometHistory = pd.concat([
                pd.Series(
                    data=True,
                    name=v.instrumentID,
                    index=pd.date_range(
                        datetime.fromisoformat(v.dateStart).astimezone(timezone.utc),
                        datetime.fromisoformat(v.dateStop).astimezone(timezone.utc),
                        freq=f"1800s"),
                        )
                for k,v in biomet.items()
                ],axis=1,sort=True)
            biometInstrumentHistory = pd.Series('',index=biometHistory.index,name='biomet')
            for sen in biometHistory.columns:
                biometInstrumentHistory.loc[biometHistory[sen].notna()] += f"-{sen}"
            biometInstrumentHistory = biometInstrumentHistory.str.strip('-')
            self.instrumentIndexMap['biomet'] = {str(uuid.uuid5(uuid.NAMESPACE_DNS,str(idx))):idx for idx in biometInstrumentHistory.unique()}
            biometInstrumentHistory = biometInstrumentHistory.replace(self.invertDict(self.instrumentIndexMap['biomet']))
        else:
            biometInstrumentHistory = pd.Series(name='biomet')
        if len(self.instrumentation['flux']):
            flux = self.instrumentation['flux']
            ecHistory = pd.concat([
                pd.Series(
                    data = True,
                    name=v.instrumentID,
                    index=pd.date_range(
                        datetime.fromisoformat(v.dateStart).astimezone(timezone.utc),
                        datetime.fromisoformat(v.dateStop).astimezone(timezone.utc),
                        freq='1800s'),
                        )
                if hasattr(v,'referenceSonic') and v.referenceSonic else
                pd.Series(
                    data = False,
                    name=v.instrumentID,
                    index=pd.date_range(
                        datetime.fromisoformat(v.dateStart).astimezone(timezone.utc),
                        datetime.fromisoformat(v.dateStop).astimezone(timezone.utc),
                        freq='1800s'),
                        )
                for k,v in flux.items() 
            ],axis=1,sort=True)
            if ecHistory.sum(axis=1).max()>1:
                exit(f"Only one reference sonic allowed per-timestamp {ecHistory.loc[ecHistory.sum(axis=1)>1]}")
            # Select reference sonics and perform positional calculations based off this for all scalar systems
            fluxInstrumentHistory = pd.Series('',index=ecHistory.index,name='flux')
            for ref in ecHistory.columns[ecHistory.sum()>0]:
                refSonic = self.instrumentation['flux'][ref]
                if refSonic.instrumentType == 'sonic_irga':
                    scalars = [ref]
                else:
                    scalars = []
                # Find all sensors referenced to the given sonic
                scalars += list(ecHistory.columns[ecHistory.loc[ecHistory[ref]==True].count()-ecHistory.loc[ecHistory[ref]==True].sum()>0])
                fluxInstrumentHistory.loc[ecHistory[ref].notna()] = ref
                for scalar in scalars:
                    fluxInstrumentHistory.loc[ecHistory[scalar].notna()] += f"-{scalar}"
                    # Convert x,y separation in northwardSeparation, eastwardSeparation using north offset
                    # geographicSeparation is method added to sonic instrumentals
                    x,y = self.instrumentation['flux'][scalar].xSeparation,self.instrumentation['flux'][scalar].ySeparation
                    self.instrumentation['flux'][ref].geographicSeparation
                    north,east=self.instrumentation['flux'][ref].geographicSeparation(x,y)
                    setattr(self.instrumentation['flux'][scalar],'northwardSeparation',north)
                    setattr(self.instrumentation['flux'][scalar],'eastwardSeparation',east)
            fluxInstrumentHistory = fluxInstrumentHistory.str.strip('-')
            self.instrumentIndexMap['flux'] = {str(uuid.uuid5(uuid.NAMESPACE_DNS,str(idx))):idx for idx in fluxInstrumentHistory.unique()}
            fluxInstrumentHistory = fluxInstrumentHistory.replace(self.invertDict(self.instrumentIndexMap['flux']))
        else:
            fluxInstrumentHistory = pd.Series(name='flux')
        self.instrumentHistory = pd.concat([biometInstrumentHistory,fluxInstrumentHistory],axis=1)
            
    def makeMetadataFiles(self):
        # Generate the template .metadata file for the group, to be filled with FileDescription at a later stage (in case different files for same configuration)
        ghgMetadata = ghgMetadataWriter()
        ghgMetadata.newFile(site_id=self.siteID,latitude=self.latitude,longitude=self.longitude,altitude=self.altitude)
        self.fluxInstrumentGroups = []
        for groupID,groupDates in self.instrumentHistory[['flux']].reset_index().groupby('flux').agg(['min','max']).iterrows():
            ghgMetadata.setDates(
                start_date=groupDates['index']['min'].isoformat(),
                stop_date=groupDates['index']['max'].isoformat(),          
                )
            for i,instrument in enumerate(self.instrumentIndexMap['flux'][groupID].split('-')):
                instrument = self.instrumentation['flux'][instrument]
                if 'sonic' in instrument.instrumentType or 'irga' in instrument.instrumentType:
                    ghgMetadata.setInstrument(
                        ix=i+1,
                        id=instrument.instrumentID,
                        model=instrument.modelName,
                        manufacturer=instrument.manufacturer,
                        height=instrument.Zm if 'sonic' in instrument.instrumentType else '',
                        north_offset=instrument.northOffset if 'sonic' in instrument.instrumentType else '',
                        vpath_length=instrument.vpathLenght if 'irga' in instrument.instrumentType else '',
                        hpath_length=instrument.hpathLenght if 'irga' in instrument.instrumentType else '',
                        northward_separation=instrument.northwardSeparation if hasattr(instrument,'northwardSeparation') else '',
                        eastward_separation=instrument.eastwardSeparation if hasattr(instrument,'eastwardSeparation') else '',
                        vertical_separation=instrument.verticalSeparation if hasattr(instrument,'verticalSeparation') else '',
                        tube_length=instrument.tubeLength if hasattr(instrument,'tubeLength') else '',
                        tube_diameter=instrument.tubeDiameter if hasattr(instrument,'tubeDiameter') else ''
                        )
            self.fluxInstrumentGroups.append(pd.DataFrame(index=[groupID],data=ghgMetadata.asDictionary(flat=True)))
        self.fluxInstrumentGroups = pd.concat(self.fluxInstrumentGroups)

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

    def loadFiles(self,writeTo,fileID,fileFormat,kwargs={},mulitProcessing=True):
        request_path = os.path.join(self.saveTo,'sourceFiles',f'{fileID}.yml')
        if os.path.isfile(request_path):
            request_kwargs = self.loadDict(request_path)
            if kwargs != {} and kwargs != request_kwargs:
                exit(f'Submitted kwargs do not match previous request.  Edit {fileID}.yml, or provide new fileID to ensure consistency.')
            else:
                kwargs = request_kwargs
        files = [file for file,md in self.sourceFileInventory[fileID].items() if md is None]
        if mulitProcessing: max_workers = None
        else: max_workers = 1

        if writeTo.endswith('Database'):
            # Multiprocessing only an option for file reading but not writing databaser format (race condition read/write conflicts)
            loader = partial(fileReader,fileFormat=fileFormat,kwargs=kwargs)
            with ProcessPoolExecutor(max_workers=max_workers) as executor:
                df = pd.concat([
                    df for df in executor.map(loader,files)
                ]).sort_index()
            db = database(databasePath=os.path.join(writeTo,'yyyy',self.siteID,fileID))
            db.loadDataFrame(df)
            outcome = {file:True for file in files}

        elif writeTo.endswith('highFrequency'):
            # For high frequency, multiprocessing can handle both read and write
            # backEnd = highFrequency(outputPath=os.path.join(writeTo,self.siteID,'yyyymm'),siteID=self.siteID,fileID=fileID,typeEnforce=True)
            writer = partial(
                hfFileLoader,
                outputPath=os.path.join(writeTo,self.siteID,'yyyymm'),
                siteID=self.siteID,
                fileID=fileID,
                fileFormat=fileFormat,
                metadataGroups=self.fluxInstrumentGroups,
                metadataTimeSeries=self.instrumentHistory['flux'],
                kwargs=kwargs)
            for file in files:
                writer(fileName=file)
            # with ProcessPoolExecutor(max_workers=max_workers) as executor:
            #     fileDescription = pd.concat([
            #         result for result in executor.map(writer,files)
            #     ])
            # outcome = {file:True for file in files}
            # fx = self.instrumentHistory.loc[fileDescription.index,'flux'].copy()
            # delete_me = fileDescription.loc[fx.isna(),('Project','file_name')]
        breakpoint()
        self.instrumentHistory.loc[fileDescription.index,'flux']
        self.sourceFileInventory[fileID] = self.sourceFileInventory[fileID] | outcome
        self.saveDict(kwargs,request_path)
        self.saveSite()
            
