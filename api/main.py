from multiprocessing import Process
import click 
from dotenv import load_dotenv

from settings.server_settings import ServerSettings
from settings.zeromq_settings import ZeroMQSettings
from settings.openai_settings import OpenAiSettings
from settings.elasticsearch_settings import ElasticSearchSettings, ESHostSettings

from runner import run_event_loop

# from backend import EmbeddingStrategy
# from backend.patterns import ZeroMQLoadBalancer

@click.group(chain=False, invoke_without_command=True)
@click.pass_context
def handler(ctx:click.core.Context):
    ctx.ensure_object(dict)
    ctx.obj["server_settings"] = ServerSettings()
    ctx.obj["zeromq_settings"] = ZeroMQSettings()
    ctx.obj["openai_settings"] = OpenAiSettings()
    ctx.obj["elasticsearch_settings"] = ElasticSearchSettings(hosts=[ESHostSettings()])

@handler.command()
@click.option("--nb_workers", default=64, help="Number of backend workers")
@click.pass_context
def launch_engine(ctx:click.core.Context, nb_workers:int):
    server_settings:ServerSettings = ctx.obj["server_settings"]
    # zeromq_settings:ZeroMQSettings = ctx.obj["zeromq_settings"]
    openai_settings:OpenAiSettings = ctx.obj["openai_settings"]
    elasticsearch_settings:ElasticSearchSettings = ctx.obj["elasticsearch_settings"]
    # cohere_settings:CohereSettings = ctx.obj["cohere_settings"]

    server_process = Process(target=run_event_loop, args=[server_settings, openai_settings, elasticsearch_settings])
    server_process.start()

    # load_balancer = ZeroMQLoadBalancer(
    #     strategy_cls=EmbeddingStrategy, 
    #     strategy_kwargs={
    #         "cohere_settings": cohere_settings
    #     }
    # )

    # sigint_was_received = load_balancer.deploy(
    #     outer_address=zeromq_settings.outer_address, 
    #     inner_address=zeromq_settings.inner_address, 
    #     nb_workers=nb_workers
    # )
    
    # if server_process.is_alive():
    #     if not sigint_was_received:
    #         server_process.terminate()
    #     server_process.join()

if __name__ == "__main__":
    load_dotenv()  # set env variables 
    handler()