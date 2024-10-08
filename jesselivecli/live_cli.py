from rich.syntax import Syntax
from rich.traceback import Traceback
from textual.app import App, ComposeResult
from textual.widgets import DirectoryTree, Footer, Header, Static, Button, Label, DataTable, Input
from textual.screen import Screen
from textual.reactive import Reactive
from textual.containers import Container, Horizontal, VerticalScroll, HorizontalScroll, Vertical
from textual.message import Message
from textual.reactive import var
from textual import work
from rich.text import Text
import sys
import asyncio
import json
import websockets
from typing import List, Dict, Optional
from jesselivecli.utils import load_config, timestamp_to_date, generate_ws_url
from rich.logging import RichHandler
import logging
import os
from datetime import datetime
from textual.binding import Binding

from pathlib import Path
from typing import Iterable
import subprocess
import re

# Import screen classes from screens.py
from jesselivecli.screens import (
    HomeScreen,
    RoutesScreen,
    ImportCandlesScreen,
    BacktestScreen,
    OptimizationScreen,
    LogScreen,
    ButtonActivatedMessage,
    RouteSelectMessage,
    SessionSelectMessage,
    SESSION_INFO,
    GENERAL_INFO,
    ROUTES_INFO,
    CANDLES_INFO,
    POSITIONS_INFO,
    ORDERS_INFO,WATCH_LIST_INFO
    
)

# Custom Header class with horizontal buttons
class CustomHeader(Container):
    def compose(self) -> ComposeResult:
        buttons = Horizontal(
            Button("Home", id="home"),
            Button("Strategies", id="strategies"),
            Button("Import Candles", id="import_candles"),
            Button("Backtest", id="backtest"),
            Button("Optimization", id="optimization"),
            Button("Log", id="log"),
            id="main_buttons"
        )
        yield buttons

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.post_message(ButtonActivatedMessage(self, event.button.id))

class JesseLiveCLIApp(App):
    log_content: Reactive[str] = Reactive("")
    CSS_PATH = "styles.tcss"  # Ensure this path points to your CSS file

    BINDINGS = [
        Binding("1","change_session('0')","Session 1", show=False),
        Binding("2", "change_session('1')", "Session 2", show=False),
        Binding("3", "change_session('2')", "Session 3", show=False),
        Binding("4", "change_session('3')", "Session 4", show=False),
        Binding("5", "change_session('4')", "Session 5", show=False),
        Binding("6", "change_session('5')", "Session 6", show=False),
        Binding("7", "change_session('6')", "Session 7", show=False),
        Binding("8", "change_session('7')", "Session 8", show=False),
        Binding("9", "change_session('8')", "Session 9", show=False),
        ("h", "switch_mode('home')", "Home"),
        ("r", "switch_mode('routes')", "Routes"),
        # ("i", "switch_mode('import_candles')", "Import Candles"),
        # ("b", "switch_mode('backtest')", "Backtest"),
        # ("o", "switch_mode('optimization')", "Optimization"),
        ("l", "switch_mode('log')", "Log"),
        ("q", "quit", "Quit"),        
    ]
    
    MODES = {
        "home": HomeScreen,
        "routes": RoutesScreen,
        "import_candles": ImportCandlesScreen,
        "backtest": BacktestScreen,
        "optimization": OptimizationScreen,
        "log": LogScreen
    }

    websocket: Optional[websockets.WebSocketClientProtocol] = None
    websocket_task = None
    command_queue = asyncio.Queue()
    messages = Reactive(None)
    id_list = Reactive([])
    log_info = Reactive("")
    log_error = Reactive("")

    id_index = 0
    start_time = 0
    initialized = False
    # default_id = ""
   
    server_config = ""
    routes_config = ""
    default_id = ""
    exchange_api_key_id = ""
    notification_api_key_id = ""
    routes_info = None
    exchange_info = None
    mode = "home"
    
    def reset_config(self):
        self.exchange_info = None
        self.routes_info = None
        self.exchange_api_key_id = ""
        self.notification_api_key_id = ""
        

    def init_config(self, server_config, routes_config, default_id):
        self.server_config = server_config
        self.routes_config = routes_config
        self.default_id = default_id
        
        self.handle_info_log("Hi there")

    def action_change_session(self, id : str):
        _id = int(id)
        _len = len(self.id_list)
        if _id < _len:
            need_reset = False
            if self.exchange_info != self.id_list[_id]:
                need_reset = True
                
            self.default_id = self.id_list[_id]
            self.id_index = _id
            if need_reset:
                self.reset_config()
            self.query_one("#session-id", Label).update(f"Session id {_id + 1}/{_len}: {self.default_id }")
            

    def setup_logger(self):
        # Create logs directory if it doesn't exist
        os.makedirs("./logs", exist_ok=True)
        
        # Generate log file name
        start_time = datetime.now().strftime("%Y%m%d%H%M%S")
        log_file = f"./logs/{start_time}.txt"
        
        # Set up logging
        logging.basicConfig(
            level=logging.INFO,
            format="%(message)s",
            datefmt="[%X]",
            handlers=[RichHandler(), logging.FileHandler(log_file)]
        )
        self.logger = logging.getLogger("rich")       

    def compose(self) -> ComposeResult:
        yield CustomHeader()
        yield Footer()

    async def on_mount(self) -> None:
        self.switch_mode("home")
        
    async def on_load(self):
        self.setup_logger()
                
        self.websocket_task = asyncio.create_task(self.start_client(self.server_config))
        # self.start_client("server.yml")
        
    # async def on_datatable_row_selected(self, event: DataTable.RowSelected) -> None:
    #     self.query_one("#overview").update(f"Row Selected: {event.row_key.value}")
    #     if event.data_table.id == "session-info":
    #         self.default_id = event.row_key.value
    async def get_active_workers(self):
        import aiohttp        
        from hashlib import sha256    
            
        cfg = load_config(self.server_config)

        data = cfg["server"]
        connection = generate_ws_url(data['host'], data['port'], data['password'])

        host = f"http://{data['host']}:{data['port']}"
        key = sha256(data['password'].encode('utf-8')).hexdigest()
        headers = {
                'Authorization': key,
                'content-type': 'application/json'
        }        
        
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.post(f'{host}/active-workers', data="") as resp:
                try:
                    ret_data = await resp.text()
                    workers = json.loads(ret_data)['data']
                except aiohttp.ClientError as e:
                    self.logger.error(f"Failed to fetch active workers: {e}")
                    return []
                except json.JSONDecodeError as e:
                    self.logger.error(f"Failed to decode JSON response: {e}")
                    return []
                except Exception as e:
                    self.logger.error(f"An unexpected error occurred: {e}")
                    return []
                return workers   
    
    async def on_route_select_message(self, message: RouteSelectMessage) -> None:
        # Check if the message is from RoutesScreen
        if isinstance(self.screen, RoutesScreen):
            # Load configuration from the selected file
            config = load_config(message.file_path)
            
            # Check if the configuration has an 'id' and update the session label
            if config:
                if 'id' in config:
                    session_id = config['id']
                    self.query_one("#route-config", Input).value = f"{message.file_path}"
                else:
                    self.query_one("#server-config", Input).value = f"{message.file_path}"
            if config and 'id' in config:
                session_id = config['id']
                active_workers = await self.get_active_workers()
                if session_id in active_workers:
                    self.query_one("#session-status", Label).update("Session status: is active")
                    # self.query_one("#start", Button).add_class("started")
                    # self.query_one("#restart", Button).add_class("started")
                    # self.query_one("#stop", Button).add_class("started")
                    self.add_class("started")
                else:
                    self.query_one("#session-status", Label).update("Session status: is not active")                    
                    # self.query_one("#start", Button).remove_class("started")
                    # self.query_one("#restart", Button).remove_class("started")
                    # self.query_one("#stop", Button).remove_class("started")
                    self.remove_class("started")
        
    async def on_button_activated_message(self, message: ButtonActivatedMessage) -> None:
        if message.button_id == "home":
            self.mode = "home"
            self.switch_mode("home")
        elif message.button_id == "strategies":
            self.mode = "strategies"
            self.switch_mode("strategies")
        elif message.button_id == "import_candles":
            self.mode = "import_candles"
            self.switch_mode("import_candles")
        elif message.button_id == "backtest":
            self.mode = "backtest"
            self.switch_mode("backtest")
        elif message.button_id == "optimization":
            self.mode = "optimization"
            self.switch_mode("optimization")
        elif message.button_id == "log":
            self.mode = "log"
            self.switch_mode("log")

            
    def restart_route(self):
        server_config = self.query_one("#server-config", Input).value
        route_file = self.query_one("#route-config", Input).value

        self.info_log(f"Restarting : {server_config} {route_file}")

        output = subprocess.run(["jesse-live-cli" ,"restart", "--server_config", server_config, "--routes_config", route_file], capture_output=True, text = True)
        
        code_view = self.query_one("#route-code", Static)
        try:
            syntax = Syntax(str(output.stdout),
                    line_numbers=True,
                    word_wrap=True,
                    indent_guides=True,
                    theme="github-dark",
                    lexer="text")            
        except Exception:
            code_view.update(Traceback(theme="github-dark", width=None))
            self.sub_title = "ERROR"
        else:
            code_view.update(syntax)        
        self.info_log(f"Restarted with return code {output.returncode}")
        if output.returncode == 0:
            self.switch_mode("home")    


    def stop_route(self):
        server_config = self.query_one("#server-config", Input).value
        route_file = self.query_one("#route-config", Input).value

        self.info_log(f"Stopping : {server_config} {route_file}")

        output = subprocess.run(["jesse-live-cli" ,"stop", "--server_config", server_config, "--routes_config", route_file], capture_output=True, text = True)
        
        code_view = self.query_one("#route-code", Static)
        try:
            syntax = Syntax(str(output.stdout),
                    line_numbers=True,
                    word_wrap=True,
                    indent_guides=True,
                    theme="github-dark",
                    lexer="text")            
        except Exception:
            code_view.update(Traceback(theme="github-dark", width=None))
            self.sub_title = "ERROR"
        else:
            code_view.update(syntax)        
        self.info_log(f"Stopped with return code {output.returncode}")
      

    def start_route(self):
        server_config = self.query_one("#server-config", Input).value
        route_file = self.query_one("#route-config", Input).value

        self.info_log(f"Starting : {server_config} {route_file}")

        output = subprocess.run(["jesse-live-cli" ,"start", "--server_config", server_config, "--routes_config", route_file], capture_output=True, text = True)
        
        code_view = self.query_one("#route-code", Static)
        try:
            syntax = Syntax(str(output.stdout),
                    line_numbers=True,
                    word_wrap=True,
                    indent_guides=True,
                    theme="github-dark",
                    lexer="text")            
        except Exception:
            code_view.update(Traceback(theme="github-dark", width=None))
            self.sub_title = "ERROR"
        else:
            code_view.update(syntax)        
        self.info_log(f"Started with return code {output.returncode}")
        if output.returncode == 0:
            self.switch_mode("home")        

                
    
    async def handle_message(self, message):
        try:
            # Process incoming messages and update state
            data = json.loads(message)
            id = data['id']
            if len(id) > 0:
                if self.default_id == "":                
                    self.default_id = id
                    self.action_change_session(str(self.id_index))
                    # self.query_one("#session-id", Label).update(f"Session id 1/1: {id}")

                if id not in self.id_list:
                    self.id_list.append(id)
                    len_id = len(self.id_list)
                    values = [
                        len_id,
                        id
                    ]
                    self.query_one("#session-info", DataTable).add_row(*values)
                    self.action_change_session(str(self.id_index))
                    # self.BINDINGS.append(("{len_id}", "change_session('{len_id}')", f"Session {len_id}"))
                
            event_info = data['event'].split(".")
            event = event_info[1] if len(event_info) == 2 else ""
            event_trading_mode = event_info[0] if len(event_info) == 2 else ""
            
            if id != self.default_id:
                return
            if self.mode != "home":
                return

            if event == 'info_log':
                self.handle_info_log(data['data']['message'])
            elif event == 'error_log':
                self.handle_error_log(data['data']['message'])
            elif event == 'exception':
                self.handle_exception(data['data']['message'])
            elif event == 'termination':
                self.handle_termination(data['data'])
            elif event == 'unexpectedTermination':
                self.handle_unexpected_termination(data['data'])      
            elif event == 'progressbar':
                self.handle_progressbar(data)
            elif event == 'general_info':
                if not self.initialized:
                    self.initialized = True
                    self.start_time = data['data']['started_at']    
                    
                self.handle_general_info(data['data'])
                if self.routes_info is None:
                    self.routes_info = data['data']['routes']
                self.handle_routes(data['data']['routes'])
                
            elif event == 'current_candles':
                self.candles = data['data']                
                self.handle_candles(data['data'])
            elif event == 'positions':
                self.positions = data['data']
                self.handle_positions(data['data'])
            elif event == 'watch_list':
                self.handle_watch_list(data['data'])
            elif event == 'orders':
                self.handle_orders(data['data'])
            else:
                self.handle_info_log(data)
                
        except Exception as e:
            self.display_error(e)
    def handle_progressbar(self, data):
        _info = data['data']
        self.handle_info_log(f"Loading data: {_info['current']}% in {_info['estimated_remaining_seconds']:.2f}s")

    def handle_session_selected(self, session_id: str) -> None:
        self.default_id = session_id
        self.display_error(f"Selected session: {session_id}")
        
    def handle_orders(self, orders: Dict[str, Dict]) -> None:
        table = self.query_one("#order-info", DataTable)
        table.clear()
        for order in orders:
            color = "[green]" if order['side'] == 'buy' else "[red]"
            values = [
                f"{color}{order['symbol']}",
                f"{color}{order['type']}",
                f"{color}{order['side']}",
                f"{color}{order['qty']:.2f}",
                f"{color}{order['price']:.2f}",
                f"{color}{order['status']}",
                f"{color}{timestamp_to_date(order['created_at'])}"                
            ]
            table.add_row(*values)

    def handle_candles(self, candles: Dict[str, Dict], round_digits: int = 3) -> None:
        """Show Route & Candles table"""
        table = self.query_one("#candle-info", DataTable)
        table.clear()
        
        
        for symbol, candle in candles.items():
            color = "[green]" if candle['open'] < candle['close'] else "[red]"
            if self.exchange_info is not None:
                exchange_info = symbol[0:symbol.find("-")]
                
            symbol = symbol[symbol.find("-") + 1:]
            values = [
                symbol,
                f"{color}{candle['open']:.{round_digits}f}",
                f"{color}{candle['close']:.{round_digits}f}",
                f"{color}{candle['high']:.{round_digits}f}",
                f"{color}{candle['low']:.{round_digits}f}",
                f"{color}{candle['volume']:.{round_digits}f}"
            ]
            table.add_row(*values)
        
        
    def handle_watch_list(self, watch_list: List[Dict]) -> None:
        try:
            table = self.query_one("#watch-list",DataTable)
            table.clear()
            for key,value in watch_list:
                values = []
                values.append(key)       
                values.append(value)  
                table.add_row(*values)       
        except Exception as e:
            self.display_error(e)

    def info_log(self, data):              
        if not self.initialized:
            return
        self.logger.info(data) 
        self.query_one("#error").update(f"LOG INFO: {data}")

    def handle_info_log(self, data):
                   
        if not self.initialized:
            return

        
        self.logger.info(data) 
        self.query_one("#error").update(f"LOG INFO: {data}")
            
        # self.log_info.append(data)
        self.log_info += f"\n{data}"
        syntax = Syntax(str(self.log_info),
                line_numbers=True,
                word_wrap=True,
                indent_guides=True,
                theme="github-dark",
                lexer="text")
        try:   
            self.query_one("#code").update(syntax)
            self.query_one("#code").scroll_home(animate=False)
        except Exception as e:
            pass
        
    def handle_error_log(self, data):
        if self.initialized:
            self.logger.error(data)
        # self.log_error.append(data)
        self.log_error += f"\n{data}"
        syntax = Syntax(self.log_error,
                line_numbers=True,
                word_wrap=True,
                indent_guides=True,
                theme="github-dark",
                lexer="text")          
        try:   
            self.query_one("#code").update(syntax)
            self.query_one("#code").scroll_home(animate=False)
        except Exception as e:
            pass

    def handle_exception(self, data):
        self.handle_error_log(f"Exception: {data}")

    def handle_termination(self, data):
        self.handle_error_log(f"Termination: {data}")

    def handle_unexpected_termination(self, data):
        self.handle_error_log(f"Unexpected Termination: {data}")

    def handle_positions(self, positions: List[Dict], round_digits: int = 3) -> None:
        try:
            table = self.query_one("#position-info", DataTable)
            table.clear()
            for position in positions:
                pnl = round(position['pnl'], round_digits) if position['type'] != 'close' else ""
                pnl_perc = round(position['pnl_perc'], round_digits) if position['type'] != 'close' else ""
                values = [
                    position['symbol'],
                    position['qty'],
                    position['entry'],
                    position['current_price'],
                    pnl,
                    pnl_perc,
                ]
                table.add_row(*[Text(str(cell), style="bold #03AC13", justify="left") for cell in values])
        except Exception as e:
            self.display_error(e)

    def handle_routes(self, routes: Dict) -> None:
        """Show Route"""
        try:         
            table = self.query_one("#route-info",DataTable)
            table.clear()            
            for route in routes:
                values = [
                    route['symbol'],
                    route['timeframe'],
                    route['strategy']
                ]

                styled_row = [
                    Text(str(cell), style="bold #03AC13", justify="left") for cell in values
                ]            
                table.add_row(*styled_row)                
        except Exception as e:
            # print(f"An error occurred: {e}")
            self.display_error(e)
            self.query_one("#overview").update(f"Error: {e}")

        
    def handle_general_info(self, infos):
        try:
            data = {info: infos[info] for info in infos}
            values = [
                f"{timestamp_to_date(data.get('started_at'))}",
                f"{timestamp_to_date(data.get('current_time'))}",
                f"{data.get('current_balance')} / {data.get('started_balance')}",
                f"{data.get('count_winning_trades')} / {data.get('count_trades')}",
                f"{data.get('pnl')}",
                f"{data.get('pnl_perc')}",
                f"{data.get('debug_mode')} / {data.get('paper_mode')}",
                f"{data.get('count_info_logs')} / {data.get('count_error_logs')}"
            ]

            table = self.query_one("#general-info", DataTable)
            table.clear()

            for i, row in enumerate(GENERAL_INFO[1:]):
                styled_row = [
                    Text(str(cell), style="bold #03AC13", justify="left") for cell in row[:1] + (values[i],)
                ]
                table.add_row(*styled_row)

        except Exception as e:
            self.display_error(e)


    def display_error(self, data):
        self.query_one("#error").update(f"Error: {str(data)}")
        code_view = self.query_one("#code", Static).update(Traceback(theme="github-dark", width=None))
        if self.initialized:
            self.logger.error(f"Error: {str(data)}")



    async def start_client(self, server_config: str):
        cfg = load_config(server_config)
        data = cfg["server"]
        connection = generate_ws_url(data['host'], data['port'], data['password'])
        await asyncio.sleep(1)  # Wait before connecting
        while True:
            try:
                print("Attempting to connect to WebSocket server...")
                async with websockets.connect(connection) as websocket:
                    self.websocket = websocket
                    print("Connected to WebSocket server.")
                    consumer_task = asyncio.create_task(self.consumer_handler(websocket))
                    producer_task = asyncio.create_task(self.producer_handler(websocket, "SessionName"))
                    done, pending = await asyncio.wait(
                        [consumer_task, producer_task],
                        return_when=asyncio.FIRST_COMPLETED,
                    )
                    for task in done:
                        if task.exception():
                            print(f"Task {task.get_name()} raised an exception: {task.exception()}")
                        else:
                            print(f"Task {task.get_name()} completed with result: {task.result()}")
                    for task in pending:
                        task.cancel()
            except websockets.ConnectionClosed as e:
                print(f"WebSocket connection closed: {e}. Reconnecting in 5 seconds...")
                await asyncio.sleep(5)  # Wait before retrying
            except Exception as e:
                print(f"An unexpected error occurred: {e}. Reconnecting in 5 seconds...")
                await asyncio.sleep(5)  # Wait before retrying

    async def consumer_handler(self, websocket):
        async for message in websocket:
            await self.handle_message(message)

    async def producer_handler(self, websocket, name):
        await websocket.send(json.dumps({"command": "join", "args": {"name": name}}))
        while True:
            command = await self.command_queue.get()
            await websocket.send(json.dumps(command))
            self.command_queue.task_done()
            
    def save_session_file(self):
        import json
        import os
        
        try:
            session_dir ="./"
            # Construct the file name using the session ID
            file_name = f"routes-{self.default_id}.json"
            file_path = os.path.join(session_dir, file_name)

            # Prepare the data to be saved
            data = {
                "id": self.default_id,
                "exchange": "" if self.exchange_info is None else self.exchange_info,
                "exchange_api_key_id": "" if self.exchange_api_key_id is None else self.exchange_api_key_id,
                "notification_api_key_id": "" if self.notification_api_key_id is None else self.notification_api_key_id,
                "routes": self.routes_info,
                "data_routes": []  # Assuming candles_info is a defined attribute
            }

            # Save the data to the fileq
            with open(file_path, "w") as file:
                json.dump(data, file, indent=2)
        except Exception as e:
            self.display_error(e)
            self.info_log(f"Session file saved as {file_path} error {e}")
        finally:
            print(f"Session file saved as {file_path}")
            self.info_log(f"Session file saved as {file_path}")
        pass
        
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Event handler called when a button is pressed."""
        if event.button.id == "start":
            # self.add_class("started")
            self.info_log("Starting session...")
            self.start_route()   
            # self.info_log("Session started")
        elif event.button.id == "restart":
            # self.add_class("started")
            self.info_log("Restarting session...")
            self.restart_route()            
            # self.info_log("Session restarted!")
        elif event.button.id == "stop":
            # self.remove_class("started")
            self.info_log("Stopping session...")
            self.stop_route()
            self.info_log("Session stopped!")
        elif event.button.id == "save":
            self.info_log("Saving session file")
            self.save_session_file()


async def run_live_cli(server_config: str, routes_config: str, default_id: str = ""):
    try:
        app = JesseLiveCLIApp()
        app.init_config(server_config, routes_config, default_id)    

        await app.run_async()
    except Exception as e:
        print(f"An unexpected error occurred: {e}. Exiting...")
        exit()
        
        