import os
import pandas as pd
from datetime import datetime
from zoneinfo import ZoneInfo
from scripts.project import project
from scripts.siteMetadata.instrumentation import hardwareModels
from scripts.submodules.helperFunctions.dataclassAddOns import dataclassFromYaml, classMethods
from scripts.submodules.helperFunctions.dictFunctions import dictFunctions
from scripts.submodules.fluxCalculator.ecf32.ecf32Create import ghgMetadataWriter

configurations = os.path.join(os.getcwd(),'configFiles')
site = dataclassFromYaml(os.path.join(configurations,'siteConfiguration.yml'),bases=(classMethods,dictFunctions))

class siteConfiguration(site):

    def validate(self,saveTo=None):
        self.checkInstruments()
        self.getInstrumentHistory()
        self.makeMetadataFiles()
        if saveTo:
            fname= os.path.join(saveTo,f"{self.siteID}_siteMetadata.yml")
            print(f"Saving to: {fname}")
            self.saveDict(self.dcToDict(self),fname)

            breakpoint()

    def checkInstruments(self):
        temp = self.instrumentation.copy()
        self.instrumentation = {}
        for kind,values in temp.items():
            self.instrumentation.setdefault(kind,{})
            if kind not in hardwareModels.keys():
                self.logError(f"Instrumentation kind = {kind} not yet supported, see/update {hardwareModels['path']}")
                
            for model in values.values():
                modelName = model['modelName'].lower()
                if modelName not in hardwareModels[kind].keys():
                    self.logError(f"Instrumentation model = {modelName} of kind = {kind} not yet supported, see/update {hardwareModels['path']}")
                model = hardwareModels[kind][modelName](**model)
                if model.dateStart == '':
                    model.dateStart = self.dateStart
                else:
                    model.dateStart = model.dateStart.isoformat()
                if model.dateStop == '':
                    model.dateStop = self.dateStop
                else:
                    model.dateStop = model.dateStop.isoformat()
                self.instrumentation[kind][model.ID] = model
        
    def getInstrumentHistory(self):
        self.instrumentHistory = pd.DataFrame()
        if len(self.instrumentation['biometSensors']):
            biometSensors = self.instrumentation['biometSensors']
            biometHistory = pd.concat([
                pd.Series(
                    data=True,
                    name=v.ID,
                    index=pd.date_range(
                        datetime.fromisoformat(v.dateStart),
                        datetime.fromisoformat(v.dateStop),
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
                        datetime.fromisoformat(v.dateStart),
                        datetime.fromisoformat(v.dateStop),
                        freq='1800s'),
                        )
                if hasattr(v,'referenceSonic') and v.referenceSonic else
                pd.Series(
                    data = False,
                    name=v.ID,
                    index=pd.date_range(
                        datetime.fromisoformat(v.dateStart),
                        datetime.fromisoformat(v.dateStop),
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


## Test Case
# siteConfiguration(
#     siteID='SCL',
#     instrumentation={
#         'dataLoggers':{'main':{'modelName':'cr1000x'}},
#         'biometSensors':{'RN':{'modelName': 'NRLite','dateStop':'2026-09-30T00:00:00+00:00'},
#                          'Tair':{'modelName':'HMP35A'}},
#         'ecSensors':{'CSAT3':{'modelName':'CSAT3','Zm':3.285,'northOffset':33,'dateStop':'2024-09-16T00:00:00+00:00'},
#                      'irgason':{'modelName': 'IRGASON','Zm':3.285,'northOffset':33,'dateStart':'2025-08-01T00:00:00+00:00'},
#                      'li7700':{'modelName': 'LI7700','xSeparation':0.45,'ySeparation':0.13,'zSeparation':0}}
#         }).validate(saveTo='/home/jskeeter/gsc-permafrost/fluxDataPipeline/testing/testProject')
