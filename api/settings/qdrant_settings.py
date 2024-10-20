
from pydantic_settings import BaseSettings
from pydantic import Field, BaseModel 
    
class QdrantSettings(BaseSettings):
    user:str=Field(validation_alias="QDRANT_USER")
    password:str=Field(validation_alias="QDRANT_PASSWORD")
    url:str=Field(validation_alias="QDRANT_URL")