import signal 
import asyncio

from fastapi import FastAPI, APIRouter
import uvicorn
import uvicorn.server

from settings.server_settings import ServerSettings
from schemas.main_entry_shemas import healthResponseModel 

from typing import List

from mapper.mapper import Mapper

class ApiServer:
    def __init__(self, server_settings:ServerSettings) -> None:
        self.host = server_settings.host
        self.port = server_settings.port

        self.api = FastAPI(
            title="Article management API",
            lifespan=self.lifespan(),
            version="1.0.0",
            description="This is the main entry point for our mini article management application"
        )
        self.api.add_api_route("/health", self.health ,methods=["GET"])

    def add_router(self, target_router:APIRouter):
        self.api.include_router(target_router)
        
    async def health(self):
        return healthResponseModel(status="good",host=self.host,port=self.port)
    
    async def release_resources(self):
        all_tasks = asyncio.all_tasks()
        blocked_tasks:List[asyncio.Task] = []
        for task in all_tasks:
            task_name = task.get_name()
            if task_name.startswith(Mapper.BLOCKED_TASK):
                task.cancel()
                blocked_tasks.append(task)

        await asyncio.gather(*blocked_tasks, return_exceptions=True)
        loop = asyncio.get_running_loop()
        loop.remove_signal_handler(sig=signal.SIGINT)
        self.server.should_exit = True 
    
    def lifespan(self):
        def inner_lifespan(app:FastAPI):
            loop = asyncio.get_running_loop()
            loop.add_signal_handler(
                sig=signal.SIGTERM,
                callback=lambda: asyncio.create_task(self.release_resources())
            )
            loop.add_signal_handler(
                sig=signal.SIGINT,
                callback=lambda: asyncio.create_task(self.release_resources())
            )
            yield 
            loop.remove_signal_handler(sig=signal.SIGTERM)
        
        return inner_lifespan

    async def run(self):
        self.config = uvicorn.Config(app=self.api, host=self.host, port=self.port)
        self.server = uvicorn.Server(config=self.config)
        await self.server.serve()