from scripts.submodules.ERA5_Data_Downloader.download_ERA5_Data import getERA5_atPoint,getERA5_IDW_at_points
from scripts.submodules.fluxCalculator.ecf32 import ecf32Create
from scripts.submodules.Binary_Database.database import database
from scripts.submodules.fileParser.parseCSI import TOB3
from scripts.siteMetadata.siteMetadata import siteConfiguration
from scripts.project import project
from matplotlib import pyplot as plt
import shutil
import os


def driveCheck(path):
    for drive in ['E:','D:','C:/','/mnt/d','/mnt/e','/mtn/c']:
        if os.path.isdir(os.path.join(drive,path)):
            path = os.path.join(drive,path)
        else: drive = None
    if drive is None:
        exit('No drive/mnt present where expected, if using wsl, try: sudo mount -t drvfs D: /mnt/d (or sudo mount -t drvfs E: /mnt/e)')
    return(path)

# sudo mount -t drvfs D: /mnt/d -o
root = 'testing'
projectName = 'testProject'
projectPath = os.path.join(root,projectName)
source = driveCheck('data-dump')


if os.path.isdir(projectPath):
    shutil.rmtree(projectPath)
pr = project(projectPath=projectPath,new=True)
pr.loadSite('SCL',template='testing/templates/SCL_template.yml')

exit('Implement better approache to dataNames.  Sacrifice simplicity in definitions for the hobo parser for more general perfomance in files with more consitent performance')
pr.loadFiles(
    siteID='SCL',
    fileID='Biomet_Data',
    fileFormat='TOB3',
    searchPath=os.path.join(source,'SCL'),
    fileNameMatch='57840_Flux_CSFormat_*.dat',

)


# pr.loadFiles(
#     siteID='SCL',
#     fileID='TS_1',
#     fileFormat='HOBOcsv',
#     searchPath=os.path.join(source,'SCL'),
#     fileNameMatch='20750528-SHSC.SSM*.csv',
#     kwargs={'dataNames':{'variableName':['TS_5cm','TS_10cm','TS_50cm','TS_100cm'],'units':['C','C','C','C']}
#     }
# )

db = database(databasePath=os.path.join(projectPath,'Database','yyyy','SCL','Biomet_Data'),errors='pass')
df = db.loadDatabase(startYear=2024,stopYear=2026)
breakpoint()

# Test Case
# siteConfiguration(
#     saveTo='testing/testProject/Sites',
#     siteID='SCL',
#     instrumentation={
#         'dataLoggers':{'main':{'modelName':'cr1000x'}},
#         'biometSensors':{'RN':{'modelName': 'NRLite','dateStop':'2026-09-30T00:00:00+00:00'},
#                          'Tair':{'modelName':'HMP35A'}},
#         'ecSensors':{'CSAT3':{'modelName':'CSAT3','Zm':3.285,'northOffset':33,'dateStop':'2024-09-16T00:00:00+00:00'},
#                      'irgason':{'modelName': 'IRGASON','Zm':3.285,'northOffset':33,'dateStart':'2025-08-01T00:00:00+00:00'},
#                      'li7700':{'modelName': 'LI7700','xSeparation':0.45,'ySeparation':0.13,'zSeparation':0}}
#         })#.validate(saveTo='testing/testProject/Sites')

# siteConfiguration.from_yaml('testing/testProject/Sites/SCL_siteMetadata.yml',kwargs={'validate':True})

# df = TOB3().read("/mnt/e/data-dump/SCL/2026/20260801/57840_Time_Series_164.dat")
# ecf32Create.ecf32Write(dataframe=df,siteID='SCL',outputPath='testing/ecf32')
# df
# breakpoint()

# ds = getERA5_atPoint(
#     dataPath=os.path.join(os.path.split(__file__)[0],'data'),
#     longitude=-135.25,
#     latitude=69.25,
#     startDate='2023-01-01',
#     stopDate='2026-12-31'
# )
# print(ds.time_series)
# dataframe = ds.time_series.copy()
# dataframe.columns = [c[1] for c in dataframe.columns]
# db = database(databasePath='testing/database/yyyy/site')
# db.loadFile(dataframe.resample(f"{db.databaseInterval}s").interpolate())
# df = db.loadDatabase(startYear=2023,stopYear=2026)


# ds = getERA5_IDW_at_points(
#     dataPath=os.path.join(os.path.split(__file__)[0],'data'),
#     latitude=[69.229,69.319],
#     longitude=[-135.257,-135.478],
#     # area=[69.26,-135.26,69.24,-135.24],
#     area = [70.25, -138.25, 68.25, -132.5],
#     pointID=['SCL','SEEP'],
#     startDate='2023-01-01',
#     stopDate='2026-12-31'
# )
# df = {}
# for site in set(ds.time_series.columns.get_level_values(0)):
#     db = database(databasePath='testing/database/yyyy/site'.replace('site',site))
#     dataframe = ds.time_series[site].copy()
#     dataframe.columns = [c[0] for c in dataframe.columns]
#     db.loadFile(dataframe.resample(f"{db.databaseInterval}s").interpolate())
#     df[site] = db.loadDatabase(startYear=2023,stopYear=2026)
# plt.figure()
# plt.plot(df['SCL'].index,df['SCL']['t2m'],label='SCL')
# plt.plot(df['SEEP'].index,df['SEEP']['t2m'],label='SEEP')
# plt.legend()
# plt.savefig(os.path.split(__file__)[0]+'/test.png')
# breakpoint()