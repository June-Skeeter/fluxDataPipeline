from scripts.submodules.ERA5_Data_Downloader.download_ERA5_Data import getERA5_atPoint
from scripts.submodules.Binary_Database.database import database
from matplotlib import pyplot as plt
import os

ds = getERA5_atPoint(
    dataPath=os.path.join(os.path.split(__file__)[0],'data'),
    longitude=-135.25,
    latitude=69.25,
    startDate='2023-01-01',
    stopDate='2026-12-31'
)
print(ds.time_series)
dataframe = ds.time_series.copy()
dataframe.columns = [c[1] for c in dataframe.columns]
db = database(databasePath='testing/database/yyyy/site')
db.loadFile(dataframe.resample(f"{db.databaseInterval}s").interpolate())
df = db.loadDatabase(startYear=2023,stopYear=2026)
plt.figure()
plt.plot(df.index,df['t2m'])
plt.savefig(os.path.split(__file__)[0]+'/test.png')
breakpoint()