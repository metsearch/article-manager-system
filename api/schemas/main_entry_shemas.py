from pydantic import BaseModel

class healthResponseModel(BaseModel):
    status:str
    host:str
    port:int