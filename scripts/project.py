# Base class of the project
from scripts.submodules.Binary_Database.database import database
from scripts.siteMetadata.siteMetadata import siteConfiguration
# from scripts.fileManagment.findFiles import findFiles
from dataclasses import dataclass, field
import geopandas as gpd
import shutil
import os

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

    def loadSite(self,siteID,template=False,validate=False):
        if template:
            print('Setting validate=True')
            validate=True
            fpath = os.path.join(self.projectPath,'Sites',siteID)
            os.makedirs(fpath,exist_ok=True)
            fpath = os.path.join(fpath,f'{siteID}_siteMetadata.yml')
            shutil.copy2(template,fpath)
        else:
            fpath = os.path.join(self.projectPath,'Sites',siteID,f"{siteID}_siteMetadata.yml")
        self.Sites[siteID] = siteConfiguration.from_yaml(fpath,kwargs={'validate':validate},preserveComments=True)
        return(self.Sites[siteID])

    def loadFiles(self,siteID,fileID,fileFormat,searchPath=None,fileNameMatch='',fileNameExclude='',outputFormat='Database',kwargs={}):
        if siteID not in self.Sites:
            self.loadSite(siteID)
        writeTo = os.path.join(self.projectPath,outputFormat)
        self.Sites[siteID].findFiles(fileID,searchPath,fileNameMatch,fileNameExclude)
        self.Sites[siteID].loadFiles(writeTo,fileID,fileFormat,kwargs,mulitProcessing=False)

    def cleanDatabase(self,siteID):
        breakpoint()

    def newProject(self):
        os.makedirs(self.projectPath)
        os.makedirs(os.path.join(self.projectPath,'Database'))
        os.makedirs(os.path.join(self.projectPath,'highFrequency'))
        os.makedirs(os.path.join(self.projectPath,'Sites'))
        gpd.GeoDataFrame(data={},index=[],geometry=gpd.points_from_xy(x=[],y=[]),crs='WGS1984').to_file(os.path.join(self.projectPath,'siteCoordinates.geojson'))

