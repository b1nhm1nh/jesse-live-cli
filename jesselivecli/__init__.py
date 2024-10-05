import asyncio
import aioconsole
from rich.prompt import Prompt
import websockets
import click

from rich.layout import Layout
from rich.live import Live
from rich.console import Console
from rich.table import Table
from rich.columns import Columns
from typing import List, Dict

import time
import json

import os
import jesse.helpers as jh
import pathlib
import yaml
import arrow

from jesselivecli.live_cli import JesseLiveCLI
    
from jesselivecli.utils import get_config, get_config_json
def validate_cwd() -> None:
    """
    make sure we're in a Jesse project
    """
    if not jh.is_jesse_project():
        print(
            jh.color(
                'Current directory is not a Jesse project. You must run commands from the root of a Jesse project. Read this page for more info: https://docs.jesse.trade/docs/getting-started/#create-a-new-jesse-project',
                'red'
            )
        )
        os._exit(1)

from hashlib import sha256

# create a Click group
@click.group()
# @click.version_option(pkg_resources.get_distribution("jesselivecli").version)
def cli() -> None:
    pass


# print(os.path.dirname(jesse))
JESSE_DIR = os.path.dirname(os.path.realpath(__file__))

def timestamp_to_date(timestamp) -> str:
    if timestamp is None:
        return ''
    if type(timestamp) == str:
        timestamp = int(timestamp)

    return str(arrow.get(timestamp))    

# Example usage
async def run_live_cli(server_yaml, routes_yaml, server_json, routes_json, default_id: str = ""):
    cli = JesseLiveCLI(server_yaml, routes_yaml, server_json, routes_json, default_id)
    await cli.run()

async def start_jesse(server_yaml, routes_yaml, server_json, routes_json):
    import aiohttp

    cfg = get_config(server_yaml) if server_json == '' else get_config_json(server_json)
    
    data = cfg["server"]
    connection = generate_ws_url(data['host'], data['port'], data['password'])

    host = f"http://{data['host']}:{data['port']}"
    key = sha256(data['password'].encode('utf-8')).hexdigest()
    headers = {
            'Authorization': key,
            'content-type': 'application/json'
        }
    exchange_api_keys = ""

    routes = get_config(routes_yaml) if routes_json == '' else get_config_json(routes_json)
    
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.post(f'{host}/active-workers', data="") as resp:
            print("========== active-workers")
            # print(resp.status)
            print(await resp.text())
            
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(f'{host}/exchange-api-keys', data="") as resp:
            print("========== exchange-api-keys")
            # print(resp.status)
            respond = await resp.text()
            print(respond)
        exchange_api_keys = json.loads(respond)
        # print(exchange_api_keys['data'][0]['id'])         
            
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(f'{host}/notification-api-keys', data="") as resp:
            print("========== notification-api-keys")
            print(resp.status)
            print(await resp.text())                   
            
    data = {}
    data['id'] = routes["id"]

    
    data['routes']                  = routes['routes']
    data['exchange']                = routes['exchange']
    data['data_routes']             = routes['data_routes']
    data['exchange_api_key_id']     = routes['exchange_api_key_id']
    data['notification_api_key_id'] = routes['notification_api_key_id']
    data['config']                  = cfg['config']
    data['debug_mode']              = cfg['debug_mode']
    data['paper_mode']              = cfg['paper_mode']
    body = json.dumps(data)

    print (f"Starting Jesse trading route {data['id']}")

    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.post(f'{host}/live', data=body) as resp:
            # print("==========")
            print(resp.status)
            # print(await resp.text())

async def stop_jesse(server_yaml, routes_yaml, server_json, routes_json):
    import aiohttp

    cfg = get_config(server_yaml) if server_json == '' else get_config_json(server_json)
    data = cfg["server"]
    connection = generate_ws_url(data['host'], data['port'], data['password'])

    host = f"http://{data['host']}:{data['port']}"
    key = sha256(data['password'].encode('utf-8')).hexdigest()
    headers = {
            'Authorization': key,
            'content-type': 'application/json'
        }

    routes = get_config(routes_yaml) if routes_json == '' else get_config_json(routes_json)
    data = {}
    data['id'] = routes["id"]    
    data['paper_mode'] = cfg['paper_mode']
    body = json.dumps(data)
    
    print (f"Stopping Jesse trading route {data['id']}")
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.post(f'{host}/cancel-live', data=body) as resp:
            print(resp.status)
            # print(await resp.text())

async def get_jesse_config(server_yaml, routes_yaml, server_json, routes_json):
    import aiohttp

    cfg = get_config(server_yaml) if server_json == '' else get_config_json(server_json)
    data = cfg["server"]
    connection = generate_ws_url(data['host'], data['port'], data['password'])

    host = f"http://{data['host']}:{data['port']}"
    key = sha256(data['password'].encode('utf-8')).hexdigest()
    headers = {
            'Authorization': key,
            'content-type': 'application/json'
        }

    routes = get_config(routes_yaml) if routes_json == '' else get_config_json(routes_json)
    data = {}
    data['id'] = 1
    data['paper_mode'] = cfg['paper_mode']
    body = json.dumps(data)
    
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.post(f'{host}/get-config', data=body) as resp:
            print(resp.status)
            # print(await resp.text())


async def shutdown_jesse(server_yaml, routes_yaml, server_json, routes_json):
    import aiohttp

    cfg = get_config(server_yaml) if server_json == '' else get_config_json(server_json)
    data = cfg["server"]
    connection = generate_ws_url(data['host'], data['port'], data['password'])

    host = f"http://{data['host']}:{data['port']}"
    key = sha256(data['password'].encode('utf-8')).hexdigest()
    headers = {
            'Authorization': key,
            'content-type': 'application/json'
        }

    routes = get_config("routes.yml")
    data = {}
    data['id'] = 1
    body = json.dumps(data)
    
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.post(f'{host}/shutdown', data=body) as resp:
            print(resp.status)
            print(await resp.text())


async def get_active_workers(server_yaml, routes_yaml, server_json, routes_json):
    import aiohttp

    cfg = get_config(server_yaml) if server_json == '' else get_config_json(server_json)
    data = cfg["server"]
    connection = generate_ws_url(data['host'], data['port'], data['password'])

    host = f"http://{data['host']}:{data['port']}"
    key = sha256(data['password'].encode('utf-8')).hexdigest()
    headers = {
            'Authorization': key,
            'content-type': 'application/json'
        }
    exchange_api_keys = ""

    routes = get_config(routes_yaml) if routes_json == '' else get_config_json(routes_json)
    
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.post(f'{host}/active-workers', data="") as resp:
            print("========== active-workers")
            print(resp.status)
            print(await resp.text())
            


@cli.command()
@click.option('--server_yaml', required=False, type=str, default='server.yml', help='Server configuration file in YAML format.')
@click.option('--routes_yaml', required=False, type=str, default='routes.yml', help='Routes configuration file in YAML format.')
@click.option('--server_json', required=False, type=str, default='', help='Server configuration file in JSON format.')
@click.option('--routes_json', required=False, type=str, default='', help='Routes configuration file in JSON format.')
def shutdown(server_yaml: str, routes_yaml: str, server_json: str, routes_json: str) -> None:
    asyncio.run(shutdown_jesse(server_yaml, routes_yaml, server_json, routes_json))

@cli.command()
@click.option('--server_yaml', required=False, type=str, default='server.yml', help='Server configuration file in YAML format.')
@click.option('--routes_yaml', required=False, type=str, default='routes.yml', help='Routes configuration file in YAML format.')
@click.option('--server_json', required=False, type=str, default='', help='Server configuration file in JSON format.')
@click.option('--routes_json', required=False, type=str, default='', help='Routes configuration file in JSON format.')
def start(server_yaml: str, routes_yaml: str, server_json: str, routes_json: str) -> None:
    asyncio.run(start_jesse(server_yaml, routes_yaml, server_json, routes_json))

@cli.command()
@click.option('--server_yaml', required=False, type=str, default='server.yml', help='Server configuration file in YAML format.')
@click.option('--routes_yaml', required=False, type=str, default='routes.yml', help='Routes configuration file in YAML format.')
@click.option('--server_json', required=False, type=str, default='', help='Server configuration file in JSON format.')
@click.option('--routes_json', required=False, type=str, default='', help='Routes configuration file in JSON format.')
def stop(server_yaml: str, routes_yaml: str, server_json: str, routes_json: str) -> None:
    asyncio.run(stop_jesse(server_yaml, routes_yaml, server_json, routes_json))

@cli.command()
@click.option('--server_yaml', required=False, type=str, default='server.yml', help='Server configuration file in YAML format.')
@click.option('--routes_yaml', required=False, type=str, default='routes.yml', help='Routes configuration file in YAML format.')
@click.option('--server_json', required=False, type=str, default='', help='Server configuration file in JSON format.')
@click.option('--routes_json', required=False, type=str, default='', help='Routes configuration file in JSON format.')
def restart(server_yaml: str, routes_yaml: str, server_json: str, routes_json: str) -> None:
    print("Restarting Jesse trading route")
    asyncio.run(stop_jesse(server_yaml, routes_yaml, server_json, routes_json))
    #delay 10s
    time.sleep(3)
    asyncio.run(start_jesse(server_yaml, routes_yaml, server_json, routes_json))



@cli.command()
@click.option('--server_yaml', required=False, type=str, default='server.yml', help='Server configuration file in YAML format.')
@click.option('--routes_yaml', required=False, type=str, default='routes.yml', help='Routes configuration file in YAML format.')
@click.option('--server_json', required=False, type=str, default='', help='Server configuration file in JSON format.')
@click.option('--routes_json', required=False, type=str, default='', help='Routes configuration file in JSON format.')
def getinfo(server_yaml: str, routes_yaml: str, server_json: str, routes_json: str) -> None:
    asyncio.run(get_active_workers(server_yaml, routes_yaml, server_json, routes_json))


@cli.command()
@click.option('--server_yaml', required=False, type=str, default='server.yml', help='Server configuration file in YAML format.')
@click.option('--routes_yaml', required=False, type=str, default='routes.yml', help='Routes configuration file in YAML format.')
@click.option('--server_json', required=False, type=str, default='', help='Server configuration file in JSON format.')
@click.option('--routes_json', required=False, type=str, default='', help='Routes configuration file in JSON format.')
@click.option('--default_id', required=False, type=str, default='', help='Listen to default id')
def run(server_yaml: str, routes_yaml: str, server_json: str, routes_json: str, default_id: str) -> None:
    asyncio.new_event_loop().run_until_complete(run_live_cli(server_yaml, routes_yaml, server_json, routes_json, default_id))
    # asyncio.run(run_live_cli(server_yaml, routes_yaml, server_json, routes_json, default_id))


async def start_proxy(server_yaml:str, server_json: str, listen_port: int):
    cfg = get_config(server_yaml) if server_json == '' else get_config_json(server_json)
    data = cfg["server"]
    connection = generate_ws_url(data['host'], data['port'], data['password'])
    # print(connection)
    host = data['host'] + ":" + str(data['port'])

    source_url = connection

    connected_clients = set()
    
    async def forward_messages(websocket):
        try:
            async with websockets.connect(source_url) as source:
                while True:
                    message = await source.recv()
                    await asyncio.gather(
                        *(client.send(message) for client in connected_clients),
                        return_exceptions=True
                    )
        except websockets.ConnectionClosed:
            print("Source connection closed")

    async def handle_client(websocket, path):
        connected_clients.add(websocket)
        try:
            await websocket.wait_closed()
        finally:
            connected_clients.remove(websocket)

    server = await websockets.serve(handle_client, "localhost", listen_port)
    forward_task = asyncio.create_task(forward_messages(None))

    print(f"Proxy server started on port {listen_port}")
    await server.wait_closed()

# Add this to the cli group
@cli.command()
@click.option('--server_yaml', required=False, type=str, default='server.yml', help='Server configuration file in YAML format.')
@click.option('--server_json', required=False, type=str, default='', help='Server configuration file in JSON format.')
@click.option('--listen_port', required=True, type=int, help='Port to listen for client connections')
def proxy(server_yaml:str, server_json: str, listen_port: int):
    asyncio.run(start_proxy(server_yaml, server_json, listen_port))

if __name__ == "__main__":
    cli()
