from scripts.submodules.helperFunctions.dictFunctions import dictFunctions
from dataclasses import dataclass, field
from fnmatch import fnmatch
import uuid
import os

fileExtensions = {
    'TOB3':'dat',
    'HOBOcsv':'csv'
}

@dataclass(kw_only=True)
class findFiles:
    fileID: str = None
    fileFormat: str
    fileNameMatch: str = None
    fileNameExclude: str = ''
    sourceFileInventory: dict = field(default_factory=dict)

    def __post_init__(self):
        if self.fileNameMatch is None:
            self.fileNameMatch = '*'
        elif not self.fileNameMatch.startswith('*'):
            self.fileNameMatch = f"*{self.fileNameMatch}"
        if self.fileNameMatch.endswith('*'):
            self.fileNameMatch += f"*.{fileExtensions[self.fileFormat]}"
        if self.fileNameExclude != '':
            if len(self.fileNameExclude)<4:
                exit('fileNameExclude length < 4 not accepted, will produce unstable results')
            else:
                self.fileNameExclude = f"*{self.fileNameExclude}"
        self.request = {
            'fileID':self.fileID,
            'fileFormat':self.fileFormat,
            'fileNameMatch':self.fileNameMatch,
            'fileNameExclude':self.fileNameExclude
        }
        self.request_id = str(uuid.uuid5(uuid.NAMESPACE_DNS,str(self.request)))
        if self.request_id not in self.sourceFileInventory:
            self.sourceFileInventory[self.request_id] = {}
        breakpoint()
        print(f'Search for {self.fileNameMatch}, exclude {self.fileExtension}')

    def search(self,searchPath):
        self.sourceFileInventory[self.request_id] = self.sourceFileInventory[self.request_id] | {
            os.path.join(dir,file):None
            for dir,_,files in os.walk(searchPath)
            for file in files if (
                fnmatch(os.path.join(dir,file),self.fileNameMatch) and 
                not fnmatch(os.path.join(dir,file),self.fileNameExclude) and
                os.path.join(dir,file) not in self.sourceFileInventory[self.request_id]
            )
        }
        breakpoint()


# findFiles(fileFormat='TOB3',fileNameMatch='Time_Series').search('/mnt/e/data-dump/SCL/2026/20260801')