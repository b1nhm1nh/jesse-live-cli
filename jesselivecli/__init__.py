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

def generate_ws_url(host: str, port: str, password: str) -> str:
    hashed_local_pass = sha256(password.encode('utf-8')).hexdigest()
    return f"ws://{host}:{port}/ws?token={hashed_local_pass}"    

# print(os.path.dirname(jesse))
JESSE_DIR = os.path.dirname(os.path.realpath(__file__))

def timestamp_to_date(timestamp) -> str:
    if timestamp is None:
        return ''
    if type(timestamp) == str:
        timestamp = int(timestamp)

    return str(arrow.get(timestamp))[:]    

def get_config(config_filename: str) -> Dict:

    cfg_file = pathlib.Path(config_filename)
    if not cfg_file.is_file():
        print(f"{config_filename} not found")
        exit()
    else:
        with open(config_filename, "r") as ymlfile:
            cfg = yaml.load(ymlfile, yaml.SafeLoader)

    return cfg

def get_config_json(config_filename: str) -> Dict:

    cfg_file = pathlib.Path(config_filename)
    if not cfg_file.is_file():
        print(f"{config_filename} not found")
        exit()
    else:
        with open(config_filename, "r") as jsonfile:
            cfg = json.load(jsonfile)

    return cfg

def refresh_infos(infos: Dict, host: str = "") -> Table:
    """Show General Info"""
    table = Table(title="Jesse Live CLI at " + host, expand=True)
    table.add_column("Started time /\nNow")
    table.add_column("Balance/ \nCurrent")
    table.add_column("Debug /\nPaper", justify="center")
    table.add_column("Infos /\nErrors", justify="center")
    table.add_column("Win /\nTotal", justify="center")
    table.add_column("PNL")
    table.add_column("PNL %")
        
    values = []
    data = {}
    for info in infos:
        data[info] = infos[info]
    # values.append(data.get("id"))
    start_time = timestamp_to_date(data.get("started_at"))
    current_time = timestamp_to_date(data.get("current_time"))
    values.append(f"{start_time} {current_time}") 
    values.append(f"{data.get('started_balance')} / {data.get('started_balance')}")
    values.append(f"{data.get('debug_mode')} / {data.get('paper_mode')}")
    values.append(f"{data.get('count_info_logs')} / {data.get('count_error_logs')}")
    values.append(f"{data.get('count_winning_trades')} / {data.get('count_trades')}")
    values.append(f"{data.get('pnl')}")     
    values.append(f"{data.get('pnl_perc')}")   

    table.add_row(*values)
    return table

def refresh_log_messages(messages: List[str]) -> Table:
    """Show log tail"""
    table = Table(title="Log messages", expand=True)

    table.add_column("Log")

    messages = messages[-16:]

    for msg in messages:
        table.add_row(msg)

    return table

round_digits_dict = {}

def refresh_candles(candles: List[str], round_digits : int = 2) -> Table:
    """Show Route & Candles table"""
    global round_digits_dict

    table = Table(title="Route & Candles", expand=True)
    table.add_column("Symbol")
    # table.add_column("Time")
    table.add_column("Open", justify="right")
    table.add_column("Close", justify="right")
    table.add_column("High", justify="right")
    table.add_column("Low", justify="right")
    table.add_column("Volume", justify="right")

    

    for symbol in candles:
        round_digits = 2
        candle_round_digits = round_digits
        if symbol in round_digits_dict:
            candle_round_digits = round_digits_dict[symbol]

        values = [symbol]
        candle = candles[symbol]
        color = "[green]" if candle['open'] < candle['close'] else "[red]"

        values.append(f"{color}{candle['open']:.{candle_round_digits}f}")
        values.append(f"{color}{candle['close']:.{candle_round_digits}f}")
        values.append(f"{color}{candle['high']:.{candle_round_digits}f}")
        values.append(f"{color}{candle['low']:.{candle_round_digits}f}")
        values.append(f"{color}{candle['volume']:.{round_digits}f}")
        table.add_row(*values)
    return table

def refresh_positions(positions: List[str]) -> Table:
    """Show Position table"""
    table = Table(title="Positions", expand=True)
    table.add_column("Symbol")
    table.add_column("Strategy")
    table.add_column("Leverage")
    table.add_column("QTY", justify="right")
    table.add_column("Entry ", justify="right")
    table.add_column("Current Price", justify="right")
    table.add_column("PNL", justify="right")
    table.add_column("PNL %", justify="right")

    for position in positions:
        values = []
        values.append(f"{position['symbol']}")
        values.append(f"{position['strategy_name']}")
        

        if position['type'] == 'close':
            values.append(f"{position['leverage']:d}")
            values.append(f"")
            values.append(f"")
            values.append(f"{position['current_price']:.2f}")
            values.append(f"")
            values.append(f"")
        else:
            color = "[green]" if position['pnl'] >0 else "[red]"
            values.append(f"{position['leverage']:d}")
            values.append(f"{color}{position['qty']:.2f}")
            values.append(f"{position['entry']:.2f}")
            values.append(f"{position['current_price']:.2f}")
            values.append(f"{color}{position['pnl']:.2f}")
            values.append(f"{color}{position['pnl_perc']:.2f}")

        table.add_row(*values)
    return table

def refresh_watch_list(watch_list: Dict) -> Table:
    """Show Watch List"""
    table = Table(title="Watch List", expand=True)
    table.add_column("Info")
    table.add_column("Data", justify="right", style="green")

    for key,value in watch_list:
        values = []
        values.append(key)       
        values.append(value)  
        table.add_row(*values)     
    return table

def refresh_routes(routes: Dict) -> Table:
    """Show Route"""
    table = Table(title="Routes", expand=True)
    # table.add_column("Exchange")
    table.add_column("Symbol", justify="right")
    table.add_column("Timeframe", justify="left")
    table.add_column("Strategy", justify="left")
    
    # log.append("[green][Info]" . routes)

    # time.sleep(600)

    for route in routes:
        values = []
        # values.append(f"{route['exchange']}")
        values.append(f"{route['symbol']}")
        values.append(f"{route['timeframe']}")
        values.append(f"{route['strategy']}")
        table.add_row(*values)
    return table


def refresh_orders(orders: Dict) -> Table:
    """Show log tail"""
    table = Table(title="Orders", expand=True)
    table.add_column("Symbol")
    table.add_column("Type")
    table.add_column("Side")
    table.add_column("QTY")
    table.add_column("Price")
    table.add_column("Status")
    table.add_column("created_at")

    for order in orders:
        color = "[green]" if order['side'] == 'buy' else "[red]"
        values = []
        # values.append(f"{type(order)} {order}")
        values.append(f"{color}{order['symbol']}")
        values.append(f"{color}{order['type']}")
        values.append(f"{color}{order['side']}")
        values.append(f"{color}{order['qty']:.2f}")
        values.append(f"{color}{order['price']:.2f}")
        values.append(f"{color}{order['status']}")
        values.append(f"{color}{timestamp_to_date(order['created_at'])}")
        table.add_row(*values)
    return table



def refresh_data():
    pass


async def run_live_cli(server_yaml, routes_yaml, server_json, routes_json, default_id: str = ""):
    id_list = []
    current_tab = 0
    running = True

    # async def handle_input():
    #     global running
    #     while running:
    #         key = await asyncio.to_thread(Prompt.ask, "Enter tab number (0-9)")
    #         if key == "q":
    #             running = False
    #         if key.isdigit() and 0 <= int(key) <= 9:
    #             current_tab = int(key) - 1
    #             if current_tab >= len(id_list):
    #                 current_tab = 0
    #         await asyncio.sleep(0.1)  # Small delay to prevent high CPU usage        

    # Get the routes, set the default id to the first route id
    routes = get_config(routes_yaml) if routes_json == '' else get_config_json(routes_json)
    route_id = routes["id"]
    if default_id == "":
        default_id = route_id

    global round_digits_dict

    for route in routes["routes"]:
        if "round_digits" in route:
            round_digits_dict[route["symbol"]] = route["round_digits"]

    layout = Layout()

    layout.split_row(
        Layout(name="left"),
        Layout(name="right"),
    )

    layout["left"].ratio = 1
    console = Console()

    log = []
    candles = []
    infos = {}
    watch_list = []
    orders = []
    routes = []
    positions = []

    cfg = get_config(server_yaml) if server_json == '' else get_config_json(server_json)
    data = cfg["server"]
    connection = generate_ws_url(data['host'], data['port'], data['password'])

    host = data['host'] + ":" + str(data['port'])

    with Live(layout, console=console, screen=True, auto_refresh=False) as live:
        async with websockets.connect(connection) as websocket:
        # async for websocket in websockets.connect(connection):
            try:
                # Run the main loop
                if websocket.open:
                  log.append("[green][Info]Connection established")

                tables = []
                tables.append(refresh_infos(infos, host))
                layout["left"].update(Columns(tables, expand=True))
                tables = []
                tables.append(refresh_log_messages(log))
                layout["right"].update(Columns(tables, expand=True))
                live.refresh()                
                while running:
                    if not websocket.open:
                        log.append("Connection closed")
                        websocket = await websockets.connect(connection)
                        break
                    else:
                        response = await websocket.recv()

                        data = json.loads(response)
                        id = data['id']
                        if default_id == "":
                            default_id = id
                        if id not in id_list:
                            id_list.append(id)

                        
                        event_info = data['event'].split(".")
                        event = ""
                        event_trading_mode = ""

                        
                        if len(event_info) == 2:
                          event = event_info[1]
                          event_trading_mode = event_info[0]

                        # other IDs
                        if id != default_id:
                            # if not (event == 'watch_list' or event == 'positions' or event == 'orders' or event == 'general_info' or event == 'current_candles'):
                            #     log.append(response)
                            continue                        


                        if event == 'info_log':
                            _log = data['data']
                            messages = _log['message'].split("\n")
                            log.append(f"[green][Info][{timestamp_to_date(_log['timestamp'])}][white] {messages[0]}")
                            for message in messages[1:]:
                                log.append(f"{message}")
                        elif event == 'error_log':
                            _log = data['data']
                            messages = _log['message'].split("\n")
                            log.append(f"[red][Error][{timestamp_to_date(_log['timestamp'])}][white] {messages[0]}")
                            for message in messages[1:]:
                                log.append(f"{message}")
                        elif event == 'exception':
                            _log = data['data']
                            log.append(f"[yellow]Exception: [white] {_log['error']}")  #{timestamp_to_date(_log['timestamp'])}
                        elif event == 'termination':
                            log.append(f"[yellow]Trade {event_trading_mode} Termination")
                            candles = []
                            positions = []
                            #running = False
                        elif event == 'unexpectedTermination':
                            _log = data['data']
                            log.append(f"[yellow]Unexpected Termination: [white] {_log['message']}")
                            candles = []
                            positions = []

                        elif event == "progressbar":
                            _info = data['data']
                            log.append(f"Loading data: {_info['current']}% in {_info['estimated_remaining_seconds']:.2f}s")
                            
                        elif event == 'current_candles':
                            candles = data['data']
                        elif event == 'positions':
                            positions = data['data']
                        elif event == 'general_info':
                            infos = data['data']
                            routes = infos['routes']
                        elif event == 'watch_list':
                            watch_list = data['data']
                        elif event == 'orders':
                            orders = data['data']
                        else:

                            log.append(response)
                        # log.append(response)

                    tables = []

                    tables.append(refresh_infos(infos, host + ". Session " + str(current_tab + 1) + "/" + str(len(id_list)) + ". ID: " + str(id)))
                    tables.append(refresh_routes(routes))
                    
                    tables.append(refresh_candles(candles, 6))
                    tables.append(refresh_positions(positions))
                    tables.append(refresh_orders(orders))
                    layout["left"].update(Columns(tables, expand=True))
                    tables = []
                    tables.append(refresh_watch_list(watch_list))
                    tables.append(refresh_log_messages(log))
                    layout["right"].update(Columns(tables, expand=True))
                    live.refresh()
                    # await asyncio.sleep(.5)  # Allow other tasks to run
            except websockets.ConnectionClosed:
                log.append("Websocket disconnected")


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
