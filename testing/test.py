from scripts.submodules.ERA5_Data_Downloader.download_ERA5_Data import getERA5_atPoint,getERA5_IDW_at_points
from scripts.submodules.Binary_Database.database import database
from scripts.project import project,newProject,site
from matplotlib import pyplot as plt
import shutil
import os

shutil.rmtree('testing/testProject')
newProject(projectPath='testing/testProject')

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