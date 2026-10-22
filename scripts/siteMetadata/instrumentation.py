from scripts.submodules.helperFunctions.dataclassAddOns import dataclassFromYaml
from dataclasses import dataclass
from datetime import datetime
import numpy as np
import random
import os

configurations = os.path.join(os.getcwd(),'configFiles','instrumentation')


@dataclass(kw_only=True)
class instrument():
    # Takes values from configs defined below, maps basic functionality for key fields
    def __post_init__(self):
        self.modelName = self.modelName.lower()
        if self.serialNumber == self.__dataclass_fields__['serialNumber'].default:
            self.serialNumber = f"{str(random.randint(0,999999)).zfill(6)}"
        if self.ID == self.__dataclass_fields__['ID'].default:
            self.ID = f"{self.modelName}_{self.serialNumber}"
        try:
            if self.dateStart != '':
                if not isinstance(self.dateStart,str):
                    self.dateStart = self.dateStart.isoformat()
                self.dateStart = datetime.fromisoformat(self.dateStart)
                if self.dateStart.tzinfo is None:
                    exit(f"Error in {self.modelName}: dates must specify UTC offset in yaml timestamp, e.g., +00:00, -06:00, etc.")
                self.dateStart = self.dateStart.isoformat()
            if self.dateStop != '':
                if not isinstance(self.dateStop,str):
                    self.dateStop = self.dateStop.isoformat()
                self.dateStop = datetime.fromisoformat(self.dateStop)
                if self.dateStop.tzinfo is None:
                    exit(f"Error in {self.modelName}: dates must specify UTC offset in yaml timestamp, e.g., +00:00, -06:00, etc.")
                self.dateStop =self.dateStop.isoformat()
        except Exception as e:
            exit(f"Error in {self.modelName}: date objects must be in iso format (with UTC offset specified), e.g. 2099-12-31T23:59:59-07:00\n\n{e}")


class calculateSeparation:
    # Zm: float
    # northOffset: float

    def geographicSeparation(self,xSeparation,ySeparation):
        # Convert to radians
        # **Note**: north offset is relative to geographic (meteorologic) north, while x,y offsets are in cartesian coordinates.  To perform the coordinate rotation properly theta must be converted to cartesian coordinate (positive is counter-clockwise from the x axis)
        theta = np.deg2rad(270-self.northOffset)
        # Calculate counter-clockwise rotation matrix
        self.R = np.array([[np.cos(theta),-np.sin(theta)],[np.sin(theta),np.cos(theta)]])
        # Evaluate rotation matrix.
        v = np.array([[xSeparation,ySeparation]])
        Rv = (self.R*v)
        Rv = Rv.sum(axis=1).round(3)
        northwardSeparation = float(Rv[1])
        eastwardSeparation = float(Rv[0])
        return(northwardSeparation,eastwardSeparation)



genericSensor = dataclassFromYaml(os.path.join(configurations,"genericSensor.yml"),(instrument,))
hardwareModels = dataclassFromYaml(os.path.join(configurations,"hardwareModels.yml"),asDataclass=False)
# Read the instrument list-config mapping
for kind in hardwareModels.keys():
    for key,value in hardwareModels[kind].items():
        filePath = os.path.join(configurations,f"{value}.yml")
        if 'sonic' in value:
            hardwareModels[kind][key] = dataclassFromYaml(filePath,(genericSensor,calculateSeparation))
        elif kind == 'dataLoggers':
            hardwareModels[kind][key] = dataclassFromYaml(filePath)
        else:
            hardwareModels[kind][key] = dataclassFromYaml(filePath,(genericSensor,))
hardwareModels['path'] = os.path.join(configurations,"hardwareModels.yml")
