

from pydantic import BaseModel

from typing import List 

class SemanticSearchReq(BaseModel):
    index:str 
    nb_neighbors:int=8
    query:str
    job_id:str 