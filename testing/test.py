from scripts.project import project
import matplotlib.pyplot as plt
import shutil
import os

if __name__ == '__main__':
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

    # pr.loadFiles(
    #     siteID='SCL',
    #     fileID='Flux_Data_v1',
    #     fileFormat='TOB3',
    #     searchPath=os.path.join(source,'SCL','2024','20240724'),
    #     fileNameExclude='*.archive*',
    #     fileNameMatch='Flux_Data*.dat',
    #     outputFormat='highFrequency',
    #     kwargs={'columnHeaderOverwrite':{
    #         'Ux':{'instrumentID':'csat3_1'},
    #         'Uy':{'instrumentID':'csat3_1'},
    #         'Uz':{'instrumentID':'csat3_1'},
    #         'Ts':{'instrumentID':'csat3_1'},
    #         'Diagnostic_CSAT':{'instrumentID':'csat3_1'},
    #         'CO2':{'instrumentID':'li7500_1'},
    #         'H2O':{'instrumentID':'li7500_1'},
    #         'press':{'instrumentID':'li7500_1'},
    #         'LI7500_diag':{'instrumentID':'li7500_1'},
    #         'LI7550_SignalStrength':{'instrumentID':'li7500_1'},
    #         'Diagnostic_7700':{'instrumentID':'li7700_1'},
    #         'CH4_density':{'instrumentID':'li7700_1'},
    #         'CH4_mole_fraction':{'instrumentID':'li7700_1'},
    #         'Temperature':{'instrumentID':'li7700_1'},
    #         'Pressure':{'instrumentID':'li7700_1'},
    #         'RSSI':{'instrumentID':'li7700_1'},
    #         }}
    # )

    # pr.loadFiles(
    #     siteID='SCL',
    #     fileID='Biomet_Data_v1',
    #     fileFormat='TOB3',
    #     searchPath=os.path.join(source,'SCL',),
    #     fileNameExclude='*.archive*',
    #     fileNameMatch='Met_Data*.dat',
    #     kwargs={'columnHeaderOverwrite':{
    #         'AirTC_Avg':{'instrumentID':'hmp35a_68'},
    #         }}
    # )

    pr.loadFiles(
        siteID='SCL',
        fileID='Flux_Data_v2',
        fileFormat='TOB3',
        searchPath=os.path.join(source,'SCL','2025','20250806'),
        fileNameExclude='*.archive*',
        fileNameMatch='*Time_Series*.dat',
        outputFormat='highFrequency',
        kwargs={
            'keepDuplicates':'shift',
            'columnHeaderOverwrite':{
                'Ux':{'instrumentID':'irgason_1'},
                'Uy':{'instrumentID':'irgason_1'},
                'Uz':{'instrumentID':'irgason_1'},
                'T_SONIC':{'instrumentID':'irgason_1'},
                'diag_sonic':{'instrumentID':'irgason_1'},
                'CO2_density':{'instrumentID':'irgason_1'},
                'CO2_density_fast_tmpr':{'units':'mg m-3','instrumentID':'irgason_1'},
                'H2O_density':{'instrumentID':'irgason_1'},
                'diag_irga':{'instrumentID':'irgason_1'},
                'T_SONIC_corr':{'instrumentID':'irgason_1'},
                'TA_1_1_1':{'instrumentID':'100k6a1a_1'},
                'PA':{'instrumentID':'irgason_1'},
                'CO2_sig_strgth':{'instrumentID':'irgason_1'},
                'H2O_sig_strgth':{'instrumentID':'irgason_1'},
                'LI7700_CH4D':{'instrumentID':'li7700_2'},
                'LI7700_pressure':{'instrumentID':'li7700_2'},
                'LI7700_temperature':{'instrumentID':'li7700_2'},
                'LI7700_sig_strgth':{'instrumentID':'li7700_2'},
                'LI7700_diag':{'instrumentID':'li7700_2'},
            }}
    )
    # pr.loadFiles(
    #     siteID='SCL',
    #     fileID='Biomet_Data_v1_2',
    #     fileFormat='MixedArray',
    #     searchPath=os.path.join(source,'SCL'),
    #     fileNameExclude=os.path.join('*SCL','2026*'),
    #     fileNameMatch='WX_data.dat',
    #     kwargs={
    #         'fileNameDef':os.path.join(source,"SCL/2024/20240914/OverWinter.DEF"),
    #         'columnHeaderOverwrite':{
    #         'AirTC_AVG':{'instrumentID':'hmp35a_68'},
    #         }}
    # )