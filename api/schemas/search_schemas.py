from pydantic import BaseModel

from typing import List 

class SemanticSearchReq(BaseModel):
    nb_neighbors:int=3
    query:str