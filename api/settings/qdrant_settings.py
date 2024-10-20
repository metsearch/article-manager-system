
from pydantic_settings import BaseSettings
from pydantic import Field, BaseModel 
    
class QdrantSettings(BaseSettings):
    host:str=Field(validation_alias="QDRANT_HOST")
    port:int=Field(validation_alias="QDRANT_PORT")