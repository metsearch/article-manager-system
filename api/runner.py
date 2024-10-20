
import asyncio 
from mapper.mapper import Mapper

from settings.server_settings import ServerSettings
from settings.openai_settings import OpenAiSettings
from settings.qdrant_settings import QdrantSettings

from routers._docs import APIDocumentation
from routers.article import Article

from server.server import ApiServer

async def run_services(
    server_settings:ServerSettings,
    openai_settings:OpenAiSettings, 
    qdrant_settings: QdrantSettings,
    ):
    
    mapper_ = Mapper(
        openai_settings=openai_settings,
        qdrant_settings=qdrant_settings,
    )
    async with mapper_ as context_mapper:
        server = ApiServer(server_settings=server_settings)
        
        docs_router = APIDocumentation(mapper=context_mapper, server=server)
        article_router = Article(mapper=context_mapper)
        
        # init the main server
        server.add_router(target_router=docs_router.router)
        server.add_router(target_router=article_router.router)


        await server.run()

def run_event_loop(
    server_settings:ServerSettings,
    openai_settings:OpenAiSettings, 
    qdrant_settings: QdrantSettings,
    ):
    asyncio.run(main=run_services(server_settings, openai_settings, qdrant_settings))
    