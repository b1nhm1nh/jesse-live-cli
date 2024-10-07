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

from jesselivecli.utils import get_config, get_config_json, generate_ws_url

class JesseLiveCLI:
    def __init__(self, server_yaml, routes_yaml, server_json, routes_json, default_id: str = ""):
        self.server_yaml = server_yaml
        self.routes_yaml = routes_yaml
        self.server_json = server_json
        self.routes_json = routes_json
        self.default_id = default_id
        self.id_list = []
        self.current_tab = 0
        self.running = True
        self.console = Console()
        self.layout = Layout()
        self.log = []
        self.candles = []
        self.infos = {}
        self.watch_list = []
        self.orders = []
        self.routes = []
        self.positions = []

    async def run(self):
        self.setup_layout()
        # cfg = self.get_config(self.server_yaml, self.server_json)
        cfg = get_config(self.server_yaml) if self.server_json == '' else get_config_json(self.server_json)
        if cfg is None:
            print("Failed to load configuration.")
            return  # Exit the run method if configuration loading fails

        # data = cfg.get("server")
        data = cfg["server"]
        if data is None:
            print("Server configuration is missing.")
            return  # Exit the run method if server configuration is missing

        connection = generate_ws_url(data['host'], data['port'], data['password'])

        async with websockets.connect(connection) as websocket:
            await self.main_loop(websocket, data['host'], data['port'])

    def setup_layout(self):
        self.layout.split_row(
            Layout(name="left"),
            Layout(name="right"),
        )
        self.layout["left"].ratio = 1

    def generate_ws_url(self, host: str, port: str, password: str) -> str:
        # Implement the logic to generate WebSocket URL
        pass

    async def main_loop(self, websocket, host, port):
        with Live(self.layout, console=self.console, screen=True, auto_refresh=False) as live:
            try:
                if websocket.open:
                    self.log.append("[green][Info]Connection established")

                self.update_layout(host, port)
                live.refresh()

                while self.running:
                    if not websocket.open:
                        self.log.append("Connection closed")
                        websocket = await websockets.connect(f"ws://{host}:{port}")
                        break
                    else:
                        response = await websocket.recv()
                        await self.process_response(response)

                    self.update_layout(host, port)
                    live.refresh()

            except websockets.ConnectionClosed:
                self.log.append("Websocket disconnected")

    async def process_response(self, response):
        data = json.loads(response)
        id = data['id']
        if self.default_id == "":
            self.default_id = id
        if id not in self.id_list:
            self.id_list.append(id)

        event_info = data['event'].split(".")
        event = event_info[1] if len(event_info) == 2 else ""
        event_trading_mode = event_info[0] if len(event_info) == 2 else ""

        if id != self.default_id:
            return

        # Process different events
        if event == 'info_log':
            self.handle_info_log(data)
        elif event == 'error_log':
            self.handle_error_log(data)
        elif event == 'exception':
            self.handle_exception(data)
        elif event == 'termination':
            self.handle_termination(event_trading_mode)
        elif event == 'unexpectedTermination':
            self.handle_unexpected_termination(data)
        elif event == "progressbar":
            self.handle_progressbar(data)
        elif event == 'current_candles':
            self.candles = data['data']
        elif event == 'positions':
            self.positions = data['data']
        elif event == 'general_info':
            self.infos = data['data']
            self.routes = self.infos['routes']
        elif event == 'watch_list':
            self.watch_list = data['data']
        elif event == 'orders':
            self.orders = data['data']
        else:
            self.log.append(response)

    def handle_info_log(self, data):
        _log = data['data']
        messages = _log['message'].split("\n")
        self.log.append(f"[green][Info][{self.timestamp_to_date(_log['timestamp'])}][white] {messages[0]}")
        for message in messages[1:]:
            self.log.append(f"{message}")

    def handle_error_log(self, data):
        _log = data['data']
        messages = _log['message'].split("\n")
        self.log.append(f"[red][Error][{self.timestamp_to_date(_log['timestamp'])}][white] {messages[0]}")
        for message in messages[1:]:
            self.log.append(f"{message}")

    def handle_exception(self, data):
        _log = data['data']
        self.log.append(f"[yellow]Exception: [white] {_log['error']}")

    def handle_termination(self, event_trading_mode):
        self.log.append(f"[yellow]Trade {event_trading_mode} Termination")
        self.candles = []
        self.positions = []

    def handle_unexpected_termination(self, data):
        _log = data['data']
        self.log.append(f"[yellow]Unexpected Termination: [white] {_log['message']}")
        self.candles = []
        self.positions = []

    def handle_progressbar(self, data):
        _info = data['data']
        self.log.append(f"Loading data: {_info['current']}% in {_info['estimated_remaining_seconds']:.2f}s")

    def update_layout(self, host, port):
        tables = []
        tables.append(self.refresh_infos(self.infos, f"{host}:{port}. Session {self.current_tab + 1}/{len(self.id_list)}. ID: {self.default_id}"))
        tables.append(self.refresh_routes(self.routes))
        tables.append(self.refresh_candles(self.candles, 6))
        tables.append(self.refresh_positions(self.positions))
        tables.append(self.refresh_orders(self.orders))
        self.layout["left"].update(Columns(tables, expand=True))

        tables = []
        tables.append(self.refresh_watch_list(self.watch_list))
        tables.append(self.refresh_log_messages(self.log))
        self.layout["right"].update(Columns(tables, expand=True))

    def refresh_infos(self, infos: Dict, host: str = "") -> Table:
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
        data = {info: infos[info] for info in infos}
        start_time = self.timestamp_to_date(data.get("started_at"))
        current_time = self.timestamp_to_date(data.get("current_time"))
        values.append(f"{start_time} {current_time}") 
        values.append(f"{data.get('started_balance')} / {data.get('current_balance')}")
        values.append(f"{data.get('debug_mode')} / {data.get('paper_mode')}")
        values.append(f"{data.get('count_info_logs')} / {data.get('count_error_logs')}")
        values.append(f"{data.get('count_winning_trades')} / {data.get('count_trades')}")
        values.append(f"{data.get('pnl')}")     
        values.append(f"{data.get('pnl_perc')}")   

        table.add_row(*values)
        return table

    def refresh_log_messages(self, messages: List[str]) -> Table:
        """Show log tail"""
        table = Table(title="Log messages", expand=True)
        table.add_column("Log")
        for msg in messages[-16:]:
            table.add_row(msg)
        return table

    def refresh_candles(self, candles: List[str], round_digits: int = 2) -> Table:
        """Show Route & Candles table"""
        table = Table(title="Route & Candles", expand=True)
        table.add_column("Symbol")
        table.add_column("Open", justify="right")
        table.add_column("Close", justify="right")
        table.add_column("High", justify="right")
        table.add_column("Low", justify="right")
        table.add_column("Volume", justify="right")

        for symbol in candles:
            candle = candles[symbol]
            color = "[green]" if candle['open'] < candle['close'] else "[red]"

            values = [
                symbol,
                f"{color}{candle['open']:.{round_digits}f}",
                f"{color}{candle['close']:.{round_digits}f}",
                f"{color}{candle['high']:.{round_digits}f}",
                f"{color}{candle['low']:.{round_digits}f}",
                f"{color}{candle['volume']:.{round_digits}f}"
            ]
            table.add_row(*values)
        return table

    def refresh_positions(self, positions: List[str]) -> Table:
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
            color = "[green]" if position['pnl'] > 0 else "[red]"
            values = [
                position['symbol'],
                position['strategy_name'],
                f"{position['leverage']:d}",
                f"{color}{position['qty']:.2f}" if position['type'] != 'close' else "",
                f"{position['entry']:.2f}" if position['type'] != 'close' else "",
                f"{position['current_price']:.2f}",
                f"{color}{position['pnl']:.2f}" if position['type'] != 'close' else "",
                f"{color}{position['pnl_perc']:.2f}" if position['type'] != 'close' else ""
            ]
            table.add_row(*values)
        return table

    def refresh_watch_list(self, watch_list: List[Dict]) -> Table:
        table = Table(title="Watch List", expand=True)
        table.add_column("Info")
        table.add_column("Data", justify="right", style="green")

        for key,value in watch_list:
            values = []
            values.append(key)       
            values.append(value)  
            table.add_row(*values)            
        # """Show Watch List"""
        # table = Table(title="Watch List", expand=True)
        # table.add_column("Info")
        # table.add_column("Data", justify="right", style="green")

        # for item in watch_list:
        #     # Assuming each item in the list is a dictionary with 'info' and 'data' keys
        #     info = item.get('info', 'N/A')
        #     data = item.get('data', 'N/A')
        #     table.add_row(info, data)
        return table

    def refresh_routes(self, routes: Dict) -> Table:
        """Show Route"""
        table = Table(title="Routes", expand=True)
        table.add_column("Symbol", justify="right")
        table.add_column("Timeframe", justify="left")
        table.add_column("Strategy", justify="left")

        for route in routes:
            values = [
                route['symbol'],
                route['timeframe'],
                route['strategy']
            ]
            table.add_row(*values)
        return table

    def refresh_orders(self, orders: Dict) -> Table:
        """Show Orders"""
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
            values = [
                f"{color}{order['symbol']}",
                f"{color}{order['type']}",
                f"{color}{order['side']}",
                f"{color}{order['qty']:.2f}",
                f"{color}{order['price']:.2f}",
                f"{color}{order['status']}",
                f"{color}{self.timestamp_to_date(order['created_at'])}"
            ]
            table.add_row(*values)
        return table

    def timestamp_to_date(self, timestamp) -> str:
        """Convert timestamp to date string"""
        if timestamp is None:
            return ''
        if isinstance(timestamp, str):
            timestamp = int(timestamp)
        return str(arrow.get(timestamp))
    
async def run_live_cli(server_yaml, routes_yaml, server_json, routes_json, default_id: str = ""):
    cli = JesseLiveCLI(server_yaml, routes_yaml, server_json, routes_json, default_id)
    await cli.run()    