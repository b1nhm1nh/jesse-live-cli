import asyncio
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
    table.add_column("started_at")
    table.add_column("current_time")
    table.add_column("Balance/Current \n balance")
    table.add_column("Debug /\nPaper", justify="center")
    table.add_column("Infos /\nErrors", justify="center")
    table.add_column("Wining trades/\nTotal trades", justify="center")
    table.add_column("PNL")
    table.add_column("PNL %")
        
    values = []
    data = {}
    for info in infos:
        data[info] = infos[info]
    values.append(timestamp_to_date(data.get("started_at")))      
    values.append(timestamp_to_date(data.get("current_time")))     
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

def refresh_candles(candles: List[str]) -> Table:
    """Show Route & Candles table"""
    table = Table(title="Route & Candles", expand=True)
    table.add_column("Symbol")
    # table.add_column("Time")
    table.add_column("Open", justify="right")
    table.add_column("Close", justify="right")
    table.add_column("High", justify="right")
    table.add_column("Low", justify="right")
    table.add_column("Volume", justify="right")

    for symbol in candles:
        values = [symbol]
        candle = candles[symbol]
        color = "[green]" if candle['open'] < candle['close'] else "[red]"

        values.append(f"{color}{candle['open']:.2f}")
        values.append(f"{color}{candle['close']:.2f}")
        values.append(f"{color}{candle['high']:.2f}")
        values.append(f"{color}{candle['low']:.2f}")
        values.append(f"{color}{candle['volume']:.2f}")
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
    table.add_column("Exchange")
    table.add_column("Symbol", justify="right")
    table.add_column("Timeframe", justify="left")
    table.add_column("Strategy", justify="left")

    for route in routes:
        values = []
        values.append(f"{route['exchange']}")
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


async def run_live_cli(server_yaml, routes_yaml, server_json, routes_json):

    layout = Layout()

    layout.split_row(
        Layout(name="left"),
        Layout(name="right"),
    )

    layout["left"].ratio = 1
    console = Console()

    log = []
    candles = []
    infos = []
    watch_list = []
    orders = []
    routes = []
    positions = []

    cfg = get_config(server_yaml) if server_json == '' else get_config_json(server_json)
    data = cfg["server"]
    connection = generate_ws_url(data['host'], data['port'], data['password'])
    # print(connection)
    host = data['host'] + ":" + str(data['port'])

    running = True
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
                        event_info = data['event'].split(".")
                        event = ""
                        event_trading_mode = ""
                        if len(event_info) == 2:
                          event = event_info[1]
                          event_trading_mode = event_info[0]

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

                    tables = []
                    tables.append(refresh_infos(infos, host))
                    tables.append(refresh_routes(routes))
                    tables.append(refresh_candles(candles))
                    tables.append(refresh_positions(positions))
                    tables.append(refresh_orders(orders))
                    layout["left"].update(Columns(tables, expand=True))
                    tables = []
                    tables.append(refresh_watch_list(watch_list))
                    tables.append(refresh_log_messages(log))
                    layout["right"].update(Columns(tables, expand=True))
                    live.refresh()
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

    routes = get_config(routes_yaml) if routes_json == '' else get_config_json(routes_json)
    data = {}
    data['id'] = 1
    data['routes'] = routes['routes']
    data['extra_routes'] = routes['extra_routes']
    data['config']     = cfg['config']
    data['debug_mode'] = cfg['debug_mode']
    data['paper_mode'] = cfg['paper_mode']
    body = json.dumps(data)
    
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.post(f'{host}/live', data=body) as resp:
            print(resp.status)
            print(await resp.text())

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
    data['id'] = 1
    data['paper_mode'] = cfg['paper_mode']
    body = json.dumps(data)
    
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.delete(f'{host}/live', data=body) as resp:
            print(resp.status)
            print(await resp.text())

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
            print(await resp.text())


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
def run(server_yaml: str, routes_yaml: str, server_json: str, routes_json: str) -> None:
    asyncio.new_event_loop().run_until_complete(run_live_cli(server_yaml, routes_yaml, server_json, routes_json))

if __name__ == "__main__":
    cli()
