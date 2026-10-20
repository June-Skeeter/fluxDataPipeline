# Base class of the project
from dataclasses import dataclass, field
import geopandas as gpd
import os

@dataclass(kw_only=True)
class project:
    projectPath: str = field(repr=False)
    siteCoordinates: dict = None

    def __post_init__(self):
        if not os.path.isdir(self.projectPath) or not os.path.isfile(os.path.join(self.projectPath,'siteCoordinates.geojson')):
            exit(f'Not valid directory {self.projectPath}')
        else:
            self.siteCoordinates = gpd.read_file(os.path.join(self.projectPath,'siteCoordinates.geojson'))

class newProject(project):

    def __post_init__(self):
        os.makedirs(self.projectPath)
        os.makedirs(os.path.join(self.projectPath,'Database'))
        os.makedirs(os.path.join(self.projectPath,'Sites'))
        gpd.GeoDataFrame(data={},index=[],geometry=gpd.points_from_xy(x=[],y=[]),crs='WGS1984').to_file(os.path.join(self.projectPath,'siteCoordinates.geojson'))
        super().__post_init__()
