from fastapi.openapi.docs import get_redoc_html, get_swagger_ui_html
from fastapi.openapi.utils import get_openapi

from fastapi import APIRouter, status

from server.server import ApiServer
from mapper.mapper import Mapper

class APIDocumentation:
    def __init__(self, mapper:Mapper, server:ApiServer) -> None:
        self.router = APIRouter(
            prefix='',
            tags=['Documentation'],
            responses={status.HTTP_200_OK: {'description': 'Documentation: openapi, redoc and swagger'}},
        )
        self.server = server
        self.mapper = mapper
        self.router.add_api_route('/', endpoint=self.get_redoc_documentation, methods=['GET'], include_in_schema=False)
        self.router.add_api_route('/openai.json', endpoint=self.openapi, methods=['GET'], include_in_schema=False)
        self.router.add_api_route('/docs', endpoint=self.get_swagger_documentation, methods=['GET'], include_in_schema=False)
    
    async def get_swagger_documentation(self):
        return get_swagger_ui_html(
            openapi_url='/openai.json',
            title=f'{self.server.api.title} - Docs'
        )
    
    async def get_redoc_documentation(self):
        return get_redoc_html(
            openapi_url='/openai.json',
            title=f'{self.server.api.title} - Redoc',
        )

    async def openapi(self):
        return get_openapi(
            title=self.server.api.title,
            version=self.server.api.version,
            description=self.server.api.description,
            routes=self.server.api.routes,
        )