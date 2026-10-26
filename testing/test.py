from scripts.project import project
import matplotlib.pyplot as plt
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

root = 'testing'
projectName = 'testProject'
projectPath = os.path.join(root,projectName)
source = driveCheck('data-dump')

if os.path.isdir(projectPath):
    shutil.rmtree(projectPath)
pr = project(projectPath=projectPath,new=True)
pr.loadSite('SCL',template='testing/templates/SCL_template.yml')

pr.loadFiles(
    siteID='SCL',
    fileID='Biomet_Data_v1',
    fileFormat='TOB3',
    searchPath=os.path.join(source,'SCL','2024','20240724'),
    fileNameExclude='*.archive*',
    fileNameMatch='Flux_Data*.dat',
    outputFormat='highFrequency',
    kwargs={'columnHeaderOverwrite':{
        'Ux':{'ID':'csat3_1'},
        'Uy':{'ID':'csat3_1'},
        'Uz':{'ID':'csat3_1'},
        'Ts':{'ID':'csat3_1'},
        'Diagnostic_CSAT':{'ID':'csat3_1'},
        'CO2':{'ID':'li7500_1'},
        'H2O':{'ID':'li7500_1'},
        'press':{'ID':'li7500_1'},
        'LI7500_diag':{'ID':'li7500_1'},
        'LI7550_SignalStrength':{'ID':'li7500_1'},
        'Diagnostic_7700':{'ID':'li7700_1'},
        'CH4_density':{'ID':'li7700_1'},
        'CH4_mole_fraction':{'ID':'li7700_1'},
        'Temperature':{'ID':'li7700_1'},
        'Pressure':{'ID':'li7700_1'},
        'RSSI':{'ID':'li7700_1'},
        }}
)

pr.loadFiles(
    siteID='SCL',
    fileID='Biomet_Data_v1',
    fileFormat='TOB3',
    searchPath=os.path.join(source,'SCL',),
    fileNameExclude='*.archive*',
    fileNameMatch='Met_Data*.dat',
    kwargs={'columnHeaderOverwrite':{
        'AirTC_Avg':{'ID':'hmp35a_68'},
        }}
)


pr.loadFiles(
    siteID='SCL',
    fileID='Biomet_Data_v1_2',
    fileFormat='MixedArray',
    searchPath=os.path.join(source,'SCL'),
    fileNameExclude=os.path.join('*SCL','2026*'),
    fileNameMatch='WX_data.dat',
    kwargs={
        'fileNameDef':os.path.join(source,"SCL/2024/20240914/OverWinter.DEF"),
        'columnHeaderOverwrite':{
        'AirTC_AVG':{'ID':'hmp35a_68'},
        }}
)