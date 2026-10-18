# Base class of the project
from dataclasses import dataclass, field


@dataclass(kw_only=True)
class project:
    projectPath: str = field(repr=False)
