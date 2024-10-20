from pydantic_settings import BaseSettings

from pydantic import Field

class ServerSettings(BaseSettings):
    host: str = Field(validation_alias="HOST")
    port: int = Field(validation_alias="PORT")
    