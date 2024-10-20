
from pydantic import BaseModel
from typing import List 
    
class Article(BaseModel):
    title:str
    field:str
    authors:List[str] 
    publication_date:str
    summary:str