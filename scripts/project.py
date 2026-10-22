# Base class of the project
from scripts.submodules.fileParser import parseCSI,parseCSV
from scripts.submodules.Binary_Database.database import database
from scripts.siteMetadata.siteMetadata import siteConfiguration
from scripts.fileManagment.findFiles import findFiles
from dataclasses import dataclass, field
import geopandas as gpd
import shutil
import os

fileParsers = {
    'TOB3':parseCSI.TOB3,
    'TOA5':parseCSI.TOA5,
    'HOBOcsv':parseCSV.HOBOcsv
}

@dataclass(kw_only=True)
class project:
    projectPath: str
    new: bool = False
    Sites: dict = field(default_factory=dict)
    # siteCoordinates: dict = None

    def __post_init__(self):
        if self.new:
            self.newProject()
        elif not os.path.isdir(self.projectPath) or not os.path.isfile(os.path.join(self.projectPath,'siteCoordinates.geojson')):
            exit(f'Not valid directory {self.projectPath}\n submit new=True to create')
        # else:
        #     self.siteCoordinates = gpd.read_file(os.path.join(self.projectPath,'siteCoordinates.geojson'))

    def loadSite(self,siteID,template=False):
        if template:
            fpath = os.path.join(self.projectPath,'Sites',siteID)
            os.makedirs(fpath,exist_ok=True)
            fpath = os.path.join(fpath,f'{siteID}_siteMetadata.yml')
            shutil.copy2(template,fpath)
        else:
            fpath = os.path.join(self.projectPath,'Sites',siteID,f"{siteID}_siteMetadata.yml")
        self.Sites[siteID] = siteConfiguration.from_yaml(fpath,kwargs={'validate':True},preserveComments=True)
        return(self.Sites[siteID])

    def loadFiles(self,siteID,fileID,fileFormat,searchPath=None,fileNameMatch='',fileNameExclude='',outputFormat='Database',kwargs={}):
        request_id = f"{fileID}_{fileFormat}"
        if siteID not in self.Sites:
            self.loadSite(siteID)
        if searchPath is not None:
            self.Sites[siteID].findFiles(request_id,fileFormat,searchPath,fileNameMatch,fileNameExclude)
        if outputFormat == 'Database':
            db = database(databasePath=os.path.join(self.projectPath,outputFormat,'yyyy',siteID,fileID))
            for file,md in self.Sites[siteID].sourceFileInventory[request_id].items():
                if md is None:
                    df = fileParsers[fileFormat](kwargs).read(file)
                    outcome = db.loadDataFrame(df)
                    if isinstance(outcome,str) and outcome.startswith('Warning'):
                        print(outcome)
                        breakpoint()
                    self.Sites[siteID].sourceFileInventory[request_id][file] = outcome

            self.Sites[siteID].saveSite()
            # breakpoint()




    # def loadFiles(self,siteID):
    #     # findFiles(fileID='Time_Series',fileFormat='TOB3',fileNameMatch='57840_Time_Series_*.dat',currentInventory=self.Sites[siteID].sourceFileInventory).search('/mnt/d/data-dump/SCL/2026/20260801')
    #     self.Sites[siteID].findFiles(
    #         fileID='Time+_Series',
    #         searchPath='/mnt/d/data-dump/SCL/2026/20260801',
    #         fileNameMatch='57840_Time_Series_*.dat',
    #     )
        # breakpoint()
        
        

    def newProject(self):
        os.makedirs(self.projectPath)
        os.makedirs(os.path.join(self.projectPath,'Database'))
        os.makedirs(os.path.join(self.projectPath,'Sites'))
        gpd.GeoDataFrame(data={},index=[],geometry=gpd.points_from_xy(x=[],y=[]),crs='WGS1984').to_file(os.path.join(self.projectPath,'siteCoordinates.geojson'))
