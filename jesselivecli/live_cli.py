from rich.syntax import Syntax
from rich.traceback import Traceback
from textual.app import App, ComposeResult
from textual.widgets import DirectoryTree, Footer, Header, Static, Button, Label, DataTable
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


# Define a custom message for button activation
class ButtonActivatedMessage(Message):
    def __init__(self, sender, button_id: str):
        super().__init__()
        self.button_id = button_id

# Define a custom message for button activation
class RouteSelectMessage(Message):
    def __init__(self, sender, file_path: str):
        super().__init__()
        self.file_path = file_path        

class SessionSelectMessage(Message):
    def __init__(self, sender, session_id: str):
        super().__init__()
        self.session_id = session_id

# Define separate screens for each button
class HomeScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Label("Home Content")
        yield Footer()

class FilteredDirectoryTree(DirectoryTree):
    def filter_paths(self, paths: Iterable[Path]) -> Iterable[Path]:
        return [path for path in paths if path.suffix in [".json", ".yml"]]

class RoutesScreen(Screen):
    BINDINGS = [
        ("f", "toggle_files", "Toggle Files"),
    ]
    show_tree = var(True)
    
    def watch_show_tree(self, show_tree: bool) -> None:
        self.set_class(show_tree, "-show-tree")
        tree_view = self.query_one("#tree-view", DirectoryTree)
        tree_view.visible = show_tree  # Toggle visibility based on show_tree
                
    def compose(self) -> ComposeResult:
        path = "./" 
        yield Label("Routes Content")
        with Container():
            yield FilteredDirectoryTree(path, id="tree-view")
            with Vertical(id="center-container"):
                with VerticalScroll(id="code-route-view"):                    
                    with Horizontal(id="button-view"):
                        yield Button("Start", id="start", variant="success")
                        yield Button("Stop", id="stop", variant="error")
                    yield Static(id="route-code", expand=True)
                    
        yield Footer()        
    def on_mount(self) -> None:
        self.query_one(DirectoryTree).focus()

    def on_directory_tree_file_selected(
        self, event: DirectoryTree.FileSelected
    ) -> None:
        event.stop()
        code_view = self.query_one("#route-code", Static)
        try:
            syntax = Syntax.from_path(
                str(event.path),
                line_numbers=True,
                word_wrap=True,
                indent_guides=True,
                theme="github-dark",
            )
            self.send_file_path_to_main_app(event)
        except Exception:
            code_view.update(Traceback(theme="github-dark", width=None))
            self.sub_title = "ERROR"
        else:
            code_view.update(syntax)
            self.query_one("#code-route-view").scroll_home(animate=True)
            self.sub_title = str(event.path)
            
    def send_file_path_to_main_app(self, event: DirectoryTree.FileSelected) -> None:
        self.post_message(RouteSelectMessage(self, event.path))

    def action_toggle_files(self) -> None:
        self.show_tree = not self.show_tree

class ImportCandlesScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Label("Import Candles Content")
        yield Footer()        

class BacktestScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Label("Backtest Content")
        yield Footer()        

class OptimizationScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Label("Optimization Content")
        yield Footer()        

"""
        table.add_column("Started time /\nNow")
        table.add_column("Balance/ \nCurrent")
        table.add_column("Debug /\nPaper", justify="center")
        table.add_column("Infos /\nErrors", justify="center")
        table.add_column("Win /\nTotal", justify="center")
        table.add_column("PNL")
        table.add_column("PNL %")
"""
SESSION_INFO = [
    ("No","Session ID"),
]
GENERAL_INFO = [
    ("Info ", "Data"),
    ("Started time:", ""),
    ("Current time:", ""),
    ("Current / Balance", ""),
    ("Win / Total", ""),
    ("PNL", ""),
    ("PNL %", ""),
    ("Debug / Paper", ""),
    ("Infos / Errors", ""),
]  
ROUTES_INFO = [
    ("Symbol", "Timeframe", "Strategy"),
]  

CANDLES_INFO = [
    ("Symbol", "Open", "Close", "High", "Low", "Volume"),
]

POSITIONS_INFO = [
    ("Symbol", "Qty", "Entry", "Price", "PNL", "PNL %"),
]  

ORDERS_INFO = [
    ("Created", "Symbol", "Type", "Side", "Price", "QTY", "Status"),
    
]

WATCH_LIST_INFO = [
    ("Info", "Data"),
    
]
            
        
class LiveScreen(Screen):
    BINDINGS = [
        ("f", "toggle_files", "Toggle Files"),
    ]
    show_tree = var(True)
    
    def watch_show_tree(self, show_tree: bool) -> None:
        self.set_class(show_tree, "-show-tree")
        logtree_view = self.query_one("#logtree-view", DirectoryTree)
        logtree_view.visible = show_tree  # Toggle visibility based on show_tree
                
    def compose(self) -> ComposeResult:
        path = "./logs/" 
        yield Label("Live Content")
        with Container():
            yield DirectoryTree(path, id="logtree-view")
            with Horizontal():
                with Vertical(id="center-container"):
                    yield Label("Session id: ", id="session-id")
                    yield DataTable(id="session-info")
                    yield Label("Routes")
                    yield DataTable(id="route-info")
                    yield Label("Candles")
                    yield DataTable(id="candle-info")
                    yield Label("Positions")
                    yield DataTable(id="position-info")
                    yield Label("Orders")
                    yield DataTable(id="order-info")
                    yield Label("LOG", id="error")
                    with VerticalScroll(id="code-view"):
                        yield Static(id="code", expand=True)
                    yield Label("Overview", id="overview")
                    yield DataTable(id="general-info")
                    yield Label("Watch List")
                    yield DataTable(id="watch-list")
        yield Footer()        
        
    def on_mount(self) -> None:
        self.query_one(DirectoryTree).focus()
        
        table = self.query_one("#session-info", DataTable)
        table.add_columns(*SESSION_INFO[0])

        table = self.query_one("#general-info", DataTable)
        table.add_columns(*GENERAL_INFO[0])

        table = self.query_one("#route-info", DataTable)
        table.add_columns(*ROUTES_INFO[0])
        
        table = self.query_one("#candle-info", DataTable)
        table.add_columns(*CANDLES_INFO[0])
        
        table = self.query_one("#watch-list", DataTable)
        table.add_columns(*WATCH_LIST_INFO[0])
        
        table = self.query_one("#position-info", DataTable)
        table.add_columns(*POSITIONS_INFO[0])

        table = self.query_one("#order-info", DataTable)
        table.add_columns(*ORDERS_INFO[0])

    def on_directory_tree_file_selected(
        self, event: DirectoryTree.FileSelected
    ) -> None:
        event.stop()
        code_view = self.query_one("#code", Static)
        try:
            syntax = Syntax.from_path(
                str(event.path),
                line_numbers=True,
                word_wrap=False,
                indent_guides=True,
                theme="github-dark",
            )
        except Exception:
            code_view.update(Traceback(theme="github-dark", width=None))
            self.sub_title = "ERROR"
        else:
            code_view.update(syntax)
            self.query_one("#code-view").scroll_home(animate=False)
            self.sub_title = str(event.path)
    
    def watch_show_tree(self, show_tree: bool) -> None:
        """Called when show_tree is modified."""
        self.set_class(show_tree, "-show-tree")
        
    def action_toggle_files(self) -> None:
        self.show_tree = not self.show_tree

    async def on_datatable_row_selected(self, event: DataTable.RowSelected) -> None:
        self.query_one("#overview").update(f"Row Selected: {event.row_key.value}")
        if event.data_table.id == "session-info":
            self.default_id = event.row_key.value

# Custom Header class with horizontal buttons
class CustomHeader(Container):
    def compose(self) -> ComposeResult:
        buttons = Horizontal(
            Button("Home", id="home"),
            Button("Strategies", id="strategies"),
            Button("Import Candles", id="import_candles"),
            Button("Backtest", id="backtest"),
            Button("Optimization", id="optimization"),
            Button("Live", id="live"),
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
        ("l", "switch_mode('live')", "Live"),
        ("q", "quit", "Quit"),        
    ]
    
    MODES = {
        "home": HomeScreen,
        "routes": RoutesScreen,
        "import_candles": ImportCandlesScreen,
        "backtest": BacktestScreen,
        "optimization": OptimizationScreen,
        "live": LiveScreen
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
   
    server_config = Reactive("")
    routes_config = Reactive("")
    default_id = Reactive("")
    

    def init_config(self, server_config, routes_config, default_id):
        self.server_config = server_config
        self.routes_config = routes_config
        self.default_id = default_id
        
        self.handle_info_log("Hi there")

    def action_change_session(self, id : str):
        _id = int(id)
        _len = len(self.id_list)
        if _id < _len:
            self.default_id = self.id_list[_id]
            self.id_index = _id
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
        self.switch_mode("live")
        
    async def on_load(self):
        self.setup_logger()
                
        self.websocket_task = asyncio.create_task(self.start_client(self.server_config))
        # self.start_client("server.yml")
        
    # async def on_datatable_row_selected(self, event: DataTable.RowSelected) -> None:
    #     self.query_one("#overview").update(f"Row Selected: {event.row_key.value}")
    #     if event.data_table.id == "session-info":
    #         self.default_id = event.row_key.value

    async def on_route_select_message(self, message: RouteSelectMessage) -> None:
        # Handle the selected route file path
        print(f"Selected route file path: {message.file_path}")
        # self.display_error(message.file_path)
        # self.handle_info_log(message.file_path)

        
    async def on_button_activated_message(self, message: ButtonActivatedMessage) -> None:
        if message.button_id == "home":
            self.switch_mode("home")
        elif message.button_id == "strategies":
            self.switch_mode("strategies")
        elif message.button_id == "import_candles":
            self.switch_mode("import_candles")
        elif message.button_id == "backtest":
            self.switch_mode("backtest")
        elif message.button_id == "optimization":
            self.switch_mode("optimization")
        elif message.button_id == "live":
            self.switch_mode("live")

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
                self.orders = data['data']
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
        self.query_one("#code").update(syntax)
        self.query_one("#code").scroll_home(animate=False)
        
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
        self.query_one("#code").update(syntax)
        self.query_one("#code").scroll_home(animate=False)

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


async def run_live_cli(server_config: str, routes_config: str, default_id: str = ""):
    try:
        app = JesseLiveCLIApp()
        app.init_config(server_config, routes_config, default_id)    
        await app.run_async()
    except Exception as e:
        print(f"An unexpected error occurred: {e}. Exiting...")
        exit()