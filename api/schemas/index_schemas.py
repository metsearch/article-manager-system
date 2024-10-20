
from pydantic import BaseModel

class IndexCreateResponse(BaseModel):
    acknowledged: bool
    shards_acknowledged: bool
    index: str

class IndexDeleteResponse(BaseModel):
    acknowledged: bool
    