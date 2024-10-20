

from pydantic_settings import BaseSettings
from pydantic import Field

class ZeroMQSettings(BaseSettings):
    outer_address:str = Field(default="ipc:///tmp/clients2broker.ipc", validation_alias="ZMQ_OUTER_ADDRESS") 
    inner_address:str = Field(default="inproc://broker2workers", validation_alias="ZMQ_INNER_ADDRESS") 
        