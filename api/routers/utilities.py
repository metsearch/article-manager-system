import json
from fastapi import APIRouter, HTTPException, UploadFile, File, status
from fastapi.responses import JSONResponse

from log_handler.log import logger 
from mapper.mapper import Mapper 

from schemas.index_schemas import IndexCreateResponse

from settings.system_settings import job_ideal_profile_generator_prompt, job_parser_prompt

class Utilities:
    def __init__(self, mapper:Mapper) -> None:
        self.router = APIRouter(
            prefix="/v1/utilities",
            tags=["Utilities"],
            responses={status.HTTP_200_OK: {"description": "Utilities......"}},
        )
        self.mapper = mapper
        
        self.router.add_api_route("/translate", methods=["POST"], endpoint=self.translate)
    
    async def translate(self, text:str, target_lang:str):
        pass
    
    async def create_index(self, index_name:str, index_schema:dict, index_settings:dict):
        index_found = await self.mapper.shared_es_client.indices.exists(index=index_name)
        if index_found:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f'{index_name} already exists, can not create an index with the same name, please delete the index if you want to create a new one or update the index'
            )

        try:
            index_creation_res = await self.mapper.shared_es_client.indices.create(
                index=index_name,
                mappings=index_schema,
                settings=index_settings
            )
            return JSONResponse(
                status_code=status.HTTP_201_CREATED,
                content={
                    'message': f'Index ({index_name}) successfully created!',
                    'result': IndexCreateResponse(**dict(index_creation_res))
                }
            )
        except Exception as e:
            logger.error(f'Error while creating an index: {str(e)}')
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )
    
    