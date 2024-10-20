
import zmq 
import zmq.asyncio as aiozmq 

import pickle
import operator as op 

import asyncio
from uuid import uuid4

from asyncio import Lock, Event 
from openai import AsyncOpenAI
from schemas.zmq_worker_schemas import WorkerResponse

from log_handler.log import logger 

from fastapi import HTTPException
from elasticsearch import AsyncElasticsearch

# from settings.zeromq_settings import ZeroMQSettings
from settings.openai_settings import OpenAiSettings
from settings.elasticsearch_settings import ElasticSearchSettings

class Mapper:
    BLOCKED_TASK:str='BLOCKED-TASK-'
    def __init__(self, openai_settings:OpenAiSettings, elasticsearch_settings:ElasticSearchSettings):
        self.openai_settings = openai_settings
        # self.zeromq_settings = zeromq_settings
        self.elasticsearch_settings = elasticsearch_settings

    # def create_socket(self, socket_type:int, connection_type:str, target_addr:str):
    #     def inner_create_socket():
    #         socket:aiozmq.Socket = self.shared_ctx.socket(socket_type=socket_type)
    #         op.attrgetter(connection_type)(socket)(addr=target_addr)  # connect or bind 
    #         downstream_exception = None 
    #         try:
    #             yield socket 
    #         except Exception as e:
    #             downstream_exception = str(e)
    #         finally:
    #             socket.close(linger=0)

    #         if downstream_exception is not None:
    #             raise HTTPException(status_code=500, detail=downstream_exception)
    #     return inner_create_socket
    
    # async def text_embedding(self, text:str):
    #     socket:aiozmq.Socket = self.shared_ctx.socket(socket_type=zmq.DEALER)
    #     socket.connect(addr=self.zeromq_settings.outer_address)
        
    #     task_id = str(uuid4())
    #     asyncio.current_task().set_name(f'{Mapper.BLOCKED_TASK}-{task_id}')
            
    #     await socket.send_multipart([b''], flags=zmq.SNDMORE)
    #     await socket.send_pyobj(text)

    #     incoming_res:WorkerResponse = None  
    #     downstream_exception = None 
    #     while True:
    #         try:
    #             incoming_event = await socket.poll(timeout=100)
    #             if incoming_event != zmq.POLLIN:
    #                 continue
    #             _, encoded_incoming_res = await socket.recv_multipart()
    #             incoming_res:WorkerResponse = pickle.loads(encoded_incoming_res)
    #             break 
    #         except asyncio.CancelledError:
    #             logger.warning(f'{task_id} was cancelled')
    #             break 
    #         except Exception as e:
    #             downstream_exception = str(e)
    #             logger.error(downstream_exception)
    #             break 
        
    #     socket.close(linger=0)
            
    #     if downstream_exception is not None:
    #         raise HTTPException(
    #             status_code=500,
    #             detail=downstream_exception
    #         )

    #     if not incoming_res.status:
    #         raise HTTPException(
    #             status_code=500,
    #             detail=incoming_res.error_message
    #         )
        
    #     return incoming_res.content
    
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
        self.shared_es_client = AsyncElasticsearch(
            hosts=list(map(lambda item: item.model_dump(), self.elasticsearch_settings.hosts)), 
            basic_auth=(self.elasticsearch_settings.user, self.elasticsearch_settings.password),
            timeout=self.elasticsearch_settings.timeout
        )
        await self.shared_es_client.__aenter__()
        information = await self.shared_es_client.info()
        print(information)
        return self 
    
    async def __aexit__(self, exc_type, exc_value, traceback):
        if exc_type is not None:
            logger.warning(exc_value)
            logger.exception(traceback)
        self.shared_ctx.term() 
        await self.shared_es_client.__aexit__()