from multiprocessing import Process
import click 
from dotenv import load_dotenv

from settings.server_settings import ServerSettings
from settings.openai_settings import OpenAiSettings
from settings.qdrant_settings import QdrantSettings

from runner import run_event_loop

@click.group(chain=False, invoke_without_command=True)
@click.pass_context
def handler(ctx:click.core.Context):
    ctx.ensure_object(dict)
    ctx.obj["server_settings"] = ServerSettings()
    ctx.obj["qdrand_settings"] = QdrantSettings()
    ctx.obj["openai_settings"] = OpenAiSettings()

@handler.command()
@click.pass_context
def launch_engine(ctx:click.core.Context):
    server_settings:ServerSettings = ctx.obj["server_settings"]
    openai_settings:OpenAiSettings = ctx.obj["openai_settings"]
    qdrant_settings:QdrantSettings = ctx.obj["qdrand_settings"]

    server_process = Process(target=run_event_loop, args=[server_settings, openai_settings, qdrant_settings])
    server_process.start()

if __name__ == "__main__":
    load_dotenv()
    handler()