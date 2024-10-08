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

# from jesselivecli.live_cli_rich import run_live_cli
from jesselivecli.live_cli import run_live_cli
    
from jesselivecli.utils import load_config, generate_ws_url
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


# # Example usage
# async def run_live_cli(server_config, routes_config, default_id: str = ""):
#     cli = JesseLiveCLI(server_config, routes_config, default_id)
#     await cli.run()

async def start_jesse(server_config, routes_config):
    import aiohttp

    cfg = load_config(server_config)
    
    data = cfg["server"]
    connection = generate_ws_url(data['host'], data['port'], data['password'])

    host = f"http://{data['host']}:{data['port']}"
    key = sha256(data['password'].encode('utf-8')).hexdigest()
    headers = {
            'Authorization': key,
            'content-type': 'application/json'
        }
    exchange_api_keys = ""

    routes = load_config(routes_config)
    
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

async def stop_jesse(server_config, routes_config):
    import aiohttp

    cfg = load_config(server_config)
    data = cfg["server"]
    connection = generate_ws_url(data['host'], data['port'], data['password'])

    host = f"http://{data['host']}:{data['port']}"
    key = sha256(data['password'].encode('utf-8')).hexdigest()
    headers = {
            'Authorization': key,
            'content-type': 'application/json'
        }

    routes = load_config(routes_config)
    data = {}
    data['id'] = routes["id"]    
    data['paper_mode'] = cfg['paper_mode']
    body = json.dumps(data)
    
    print (f"Stopping Jesse trading route {data['id']}")
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.post(f'{host}/cancel-live', data=body) as resp:
            print(resp.status)
            # print(await resp.text())

async def get_jesse_config(server_config, routes_config):
    import aiohttp

    cfg = load_config(server_config)
    data = cfg["server"]
    connection = generate_ws_url(data['host'], data['port'], data['password'])

    host = f"http://{data['host']}:{data['port']}"
    key = sha256(data['password'].encode('utf-8')).hexdigest()
    headers = {
            'Authorization': key,
            'content-type': 'application/json'
        }

    routes = load_config(routes_config)
    data = {}
    data['id'] = 1
    data['paper_mode'] = cfg['paper_mode']
    body = json.dumps(data)
    
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.post(f'{host}/get-config', data=body) as resp:
            print(resp.status)
            # print(await resp.text())


async def shutdown_jesse(server_config, routes_config):
    import aiohttp

    cfg = load_config(server_config)
    data = cfg["server"]
    connection = generate_ws_url(data['host'], data['port'], data['password'])

    host = f"http://{data['host']}:{data['port']}"
    key = sha256(data['password'].encode('utf-8')).hexdigest()
    headers = {
            'Authorization': key,
            'content-type': 'application/json'
        }

    routes = load_config(routes_config)
    data = {}
    data['id'] = 1
    body = json.dumps(data)
    
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.post(f'{host}/shutdown', data=body) as resp:
            print(resp.status)
            print(await resp.text())


async def get_active_workers(server_config, routes_config):
    import aiohttp

    cfg = load_config(server_config)
    data = cfg["server"]
    connection = generate_ws_url(data['host'], data['port'], data['password'])

    host = f"http://{data['host']}:{data['port']}"
    key = sha256(data['password'].encode('utf-8')).hexdigest()
    headers = {
            'Authorization': key,
            'content-type': 'application/json'
        }
    exchange_api_keys = ""

    routes = load_config(routes_config)
    
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.post(f'{host}/active-workers', data="") as resp:
            print("========== active-workers")
            print(resp.status)
            print(await resp.text())
            


@cli.command()
@click.option('--server_config', required=False, type=str, default='server.yml', help='Server configuration file in YAML / JSON format.')
@click.option('--routes_config', required=False, type=str, default='routes.yml', help='Routes configuration file in YAML / JSON format.')
def shutdown(server_config: str, routes_config: str) -> None:
    asyncio.run(shutdown_jesse(server_config, routes_config))

@cli.command()
@click.option('--server_config', required=False, type=str, default='server.yml', help='Server configuration file in YAML / JSON format.')
@click.option('--routes_config', required=False, type=str, default='routes.yml', help='Routes configuration file in YAML / JSON format.')
def start(server_config: str, routes_config: str) -> None:
    asyncio.run(start_jesse(server_config, routes_config))

@cli.command()
@click.option('--server_config', required=False, type=str, default='server.yml', help='Server configuration file in YAML / JSON format.')
@click.option('--routes_config', required=False, type=str, default='routes.yml', help='Routes configuration file in YAML / JSON format.')
def stop(server_config: str, routes_config: str) -> None:
    asyncio.run(stop_jesse(server_config, routes_config))

@cli.command()
@click.option('--server_config', required=False, type=str, default='server.yml', help='Server configuration file in YAML / JSON format.')
@click.option('--routes_config', required=False, type=str, default='routes.yml', help='Routes configuration file in YAML / JSON format.')
def restart(server_config: str, routes_config: str) -> None:
    print("Restarting Jesse trading route")
    asyncio.run(stop_jesse(server_config, routes_config))
    time.sleep(2)
    asyncio.run(start_jesse(server_config, routes_config))



@cli.command()
@click.option('--server_config', required=False, type=str, default='server.yml', help='Server configuration file in YAML / JSON format.')
@click.option('--routes_config', required=False, type=str, default='routes.yml', help='Routes configuration file in YAML / JSON format.')
def getinfo(server_config: str, routes_config: str) -> None:
    asyncio.run(get_active_workers(server_config, routes_config))


@cli.command()
@click.option('--server_config', required=False, type=str, default='server.yml', help='Server configuration file in YAML / JSON format.')
@click.option('--routes_config', required=False, type=str, default='routes.yml', help='Routes configuration file in YAML / JSON format.')
@click.option('--default_id', required=False, type=str, default='', help='Listen to default id')
def run(server_config: str, routes_config: str, default_id: str) -> None:
    asyncio.new_event_loop().run_until_complete(run_live_cli(server_config, routes_config, default_id))


async def start_proxy(server_config: str, listen_port: int):
    cfg = load_config(server_config)
    data = cfg["server"]
    connection = generate_ws_url(data['host'], data['port'], data['password'])
    # print(connection)
    host = data['host'] + ":" + str(data['port'])

    source_url = connection

    connected_clients = set()
    
    async def forward_messages(websocket):
        while True:
            try:
                print("Connecting ...")
                async with websockets.connect(source_url) as source:
                    print("Connected to server, Forwarding messages....")
                    while True:
                        message = await source.recv()
                        await asyncio.gather(
                            *(client.send(message) for client in connected_clients),
                            return_exceptions=True
                        )
            except websockets.ConnectionClosed as e:
                print(f"Connection closed: {e}. Attempting to reconnect in 5s...")
                await asyncio.sleep(5)  # Wait for 5 seconds before retrying
            except websockets.InvalidURI as e:
                print(f"Invalid URI: {e}. Check the WebSocket URL.")
                break  # Exit the loop if the URI is invalid
            except websockets.InvalidHandshake as e:
                print(f"Invalid handshake: {e}. Check the server configuration.")
                break  # Exit the loop if the handshake fails
            except Exception as e:
                print(f"An unexpected error occurred: {e}. Retrying in 5s...")
                await asyncio.sleep(5)  # Wait for 5 seconds before retrying

    async def handle_client(websocket, path):
        print("New client connected!")
        connected_clients.add(websocket)
        try:
            await websocket.wait_closed()
        finally:
            connected_clients.remove(websocket)
            print("Client disconnected!")
            

    server = await websockets.serve(handle_client, "localhost", listen_port)
    forward_task = asyncio.create_task(forward_messages(None))

    print(f"Proxy server started on port {listen_port}")
    await server.wait_closed()

# Add this to the cli group
@cli.command()
@click.option('--server_config', required=False, type=str, default='server.yml', help='Server configuration file in YAML / JSON format.')
@click.option('--listen_port', required=True, type=int, help='Port to listen for client connections')
def proxy(server_config: str,  listen_port: int):
    asyncio.run(start_proxy(server_config, listen_port))

if __name__ == "__main__":
    cli()