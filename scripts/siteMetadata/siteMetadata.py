import os
import pandas as pd
from datetime import datetime, timezone
from dataclasses import dataclass, field
from scripts.siteMetadata.instrumentation import hardwareModels
from scripts.submodules.helperFunctions.dataclassAddOns import dataclassFromYaml, classMethods
from scripts.submodules.helperFunctions.dictFunctions import dictFunctions
from scripts.submodules.fluxCalculator.ecf32.ecf32Create import ghgMetadataWriter

configurations = os.path.join(os.getcwd(),'configFiles')
site = dataclassFromYaml(os.path.join(configurations,'siteConfiguration.yml'),bases=(classMethods,dictFunctions))

@dataclass(kw_only=True)
class siteConfiguration(site):
    saveTo: str = field(default=None,repr=False)
    validate: bool = field(default=False,repr=False)

    def __post_init__(self):
        if hasattr(self,'__classmethod_flag__') and self.__classmethod_flag__['method'] == 'from_yaml':
            self.source = self.__classmethod_flag__['source']
            readFrom = os.path.split(self.__classmethod_flag__['fpath'])[0]
            fname= os.path.join(readFrom,f"{self.siteID}_instrumentHistory.csv")
            if not os.path.isfile(fname) or self.validate:
                self.validateMetadata(saveTo=readFrom)
            self.instrumentHistory = pd.read_csv(fname,index_col=[0],header=[0])
            fname= os.path.join(readFrom,f"{self.siteID}_ecInstrumentGroups.csv")
            self.ecInstrumentGroups = pd.read_csv(fname,index_col=[0],header=[0,1])
        else:
            self.source = None
            if self.saveTo:
                self.validateMetadata(saveTo=self.saveTo)

    def validateMetadata(self,saveTo=None):
        print(f"validating {self.siteID}_siteMetadata.yml")
        # if loaded from yaml, insert missing parameters, preserve flags
        if self.source:
            self.checkSiteParameters()
        self.checkInstruments()
        self.getInstrumentHistory()
        self.makeMetadataFiles()
        if saveTo:
            os.makedirs(saveTo,exist_ok=True)
            fname= os.path.join(saveTo,f"{self.siteID}_siteMetadata.yml")
            if not os.path.isfile(fname):
                print(f"Saving siteMetadata to: {fname}")
                self.saveDict(self.dcToDict(self),fname)
            elif self.source:
                self.saveDict(self.source,fname)
                breakpoint()
            fname= os.path.join(saveTo,f"{self.siteID}_instrumentHistory.csv")
            print(f"Saving instrumentHistory to: {fname}")
            self.instrumentHistory.to_csv(fname)
            fname= os.path.join(saveTo,f"{self.siteID}_ecInstrumentGroups.csv")
            print(f"Saving ecInstrumentGroups to: {fname}")
            self.ecInstrumentGroups.to_csv(fname)

    def checkSiteParameters(self):
        for key in site.__annotations__.keys():
            value = getattr(self,key)
            if key.startswith('date'):
                if isinstance(value,str):
                    temp = datetime.fromisoformat(value)
                else:
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

