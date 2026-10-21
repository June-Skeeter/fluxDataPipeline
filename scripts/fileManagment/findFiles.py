from dataclasses import dataclass, field
from fnmatch import fnmatch
import os

fileExtensions = {
    'TOB3':'dat',
    'HOBOcsv':'csv'
}

@dataclass(kw_only=True)
class findFiles:
    fileFormat: str
    fileExtension: str = None
    fileNameMatch: str = None
    fileNameExclude: str = ''
    currentInventory: list = field(default_factory=list)

    def __post_init__(self):
        if self.fileExtension is None:
            self.fileExtension = fileExtensions[self.fileFormat]
        if self.fileNameMatch is None:
            self.fileNameMatch = f"*.{self.fileExtension}"
        elif not self.fileNameMatch.startswith('*'):
            self.fileNameMatch = f"*{self.fileNameMatch}"
            if not self.fileNameMatch.endswith(self.fileExtension):
                self.fileNameMatch += f"*.{self.fileExtension}"
        if self.fileNameExclude != '':
            if len(self.fileNameExclude)<4:
                exit('fileNameExclude length < 4 not accepted, will produce unstable results')
            else:
                self.fileNameExclude = f"*{self.fileNameExclude}"
        print(f'Search for {self.fileNameMatch}, exclude {self.fileExtension}')

    def search(self,searchPath):
        newFiles = [
            os.path.join(dir,file)
            for dir,_,files in os.walk(searchPath)
            for file in files if (
                fnmatch(os.path.join(dir,file),self.fileNameMatch) and 
                not fnmatch(os.path.join(dir,file),self.fileNameExclude) and
                os.path.join(dir,file) not in self.currentInventory
            )
            ]
        breakpoint()


# findFiles(fileFormat='TOB3',fileNameMatch='Time_Series').search('/mnt/e/data-dump/SCL/2026/20260801')