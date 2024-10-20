from typing import Any, Optional

from pydantic import BaseModel
from enum import Enum 

class WorkerStatus(bytes, Enum):
    FREE:bytes=b'FREE'
    DONE:bytes=b'DONE'

class WorkerResponse(BaseModel):
    status:bool=True 
    content:Any=None
    error_message:Optional[str]=None 