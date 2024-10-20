import zmq.asyncio as aiozmq 

from asyncio import Lock, Event 
from openai import AsyncOpenAI

from log_handler.log import logger 

from elasticsearch import AsyncElasticsearch
import qdrant_client

from settings.openai_settings import OpenAiSettings
from settings.qdrant_settings import QdrantSettings

class Mapper:
    BLOCKED_TASK:str='BLOCKED-TASK-'
    def __init__(self, openai_settings:OpenAiSettings, qdrant_settings: QdrantSettings):
        self.openai_settings = openai_settings
        self.qdrant_settings = qdrant_settings
    
    async def get_embedding(self, text:str):
        print('start..embed')
        text = text.replace("\n", " ")
        response = await self.shared_openai_client.embeddings.create(input=[text], model="text-embedding-3-small")
        print('end..embed')
        return response.data[0].embedding
    
    async def __aenter__(self):
        self.shared_ctx = aiozmq.Context()
        self.shared_lock = Lock()
        self.shared_event = Event()
        self.shared_openai_client = AsyncOpenAI(api_key=self.openai_settings.api_key)
        self.shared_qdrant_client = qdrant_client.AsyncQdrantClient(self.qdrant_settings.url)
        return self 
    
    async def __aexit__(self, exc_type, exc_value, traceback):
        if exc_type is not None:
            logger.warning(exc_value)
            logger.exception(traceback)
        self.shared_ctx.term() 