

from pydantic_settings import BaseSettings
from pydantic import Field, BaseModel 

from typing import List, Tuple

class ESHostSettings(BaseSettings):
    host:str=Field(validation_alias="ELASTICSEARCH_HOST")
    port:int=Field(validation_alias="ELASTICSEARCH_PORT")
    scheme:str=Field(validation_alias="ELASTICSEARCH_PROTOCOL") 
    
class ElasticSearchSettings(BaseSettings):
    hosts:List[ESHostSettings]
    user:str=Field(validation_alias="ELASTICSEARCH_USER")
    password:str=Field(validation_alias="ELASTICSEARCH_PASSWORD")
    timeout:int=Field(validation_alias="ELASTICSEARCH_TIMEOUT")