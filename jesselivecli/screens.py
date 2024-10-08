from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import DirectoryTree, Footer, Label, Button, Static, DataTable
from textual.containers import Container, Horizontal, VerticalScroll, Vertical
from textual.reactive import var
from textual.message import Message
from rich.syntax import Syntax
from rich.traceback import Traceback
from rich.text import Text
from typing import Iterable
from pathlib import Path


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
        

# Define a custom message for button activation
class ButtonActivatedMessage(Message):
    def __init__(self, sender, button_id: str, message: str):
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

class FilteredDirectoryTree(DirectoryTree):
    def filter_paths(self, paths: Iterable[Path]) -> Iterable[Path]:
        return [path for path in paths if path.suffix in [".json", ".yml", ".txt"]]

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
                        yield Button("Restart", id="restart", variant="success")
                        yield Button("Stop", id="stop", variant="error")
                    yield Label("Session ID:", id="session")                        
                    yield Label("Route file:", id="route-file")                        
                    yield Label("LOG", id="error")
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
            self.query_one("#route-file", Label).update(f"Route file: [{event.path}]")
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

# Define separate screens for each button
class LogScreen(Screen):
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
        yield Label("Log Screen")
        with Container():
            yield FilteredDirectoryTree(path, id="logtree-view")
            with Vertical(id="center-container"):
                with VerticalScroll(id="code-log-view"):                    
                    # with Horizontal(id="button-view"):
                    #     yield Button("Refresh", id="refresh", variant="success")
                    yield Static(id="log-code", expand=True)
                    
        yield Footer()        
    def on_mount(self) -> None:
        self.query_one(DirectoryTree).focus()

    def on_directory_tree_file_selected(
        self, event: DirectoryTree.FileSelected
    ) -> None:
        event.stop()
        code_view = self.query_one("#log-code", Static)
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
            self.query_one("#code-log-view").scroll_home(animate=True)
            self.sub_title = str(event.path)
            
    def send_file_path_to_main_app(self, event: DirectoryTree.FileSelected) -> None:
        self.post_message(RouteSelectMessage(self, event.path))

    def action_toggle_files(self) -> None:
        self.show_tree = not self.show_tree

class HomeScreen(Screen):
    # BINDINGS = [
    #     ("f", "toggle_files", "Toggle Files"),
    # ]
    show_tree = var(True)
    
    def watch_show_tree(self, show_tree: bool) -> None:
        self.set_class(show_tree, "-show-tree")
        logtree_view = self.query_one("#logtree-view", DirectoryTree)
        logtree_view.visible = show_tree  # Toggle visibility based on show_tree
                
    def compose(self) -> ComposeResult:
        path = "./logs/" 
        yield Label("Home Screen")
        with Container():
            yield DirectoryTree(path, id="hometree-view")
            with Horizontal():
                with Vertical(id="center-container"):
                    with Horizontal(id="session-region"):
                        with Vertical():
                            yield DataTable(id="session-info")  
                            yield Label("Session id: ", id="session-id")
                        yield Button("Save Session", id="save", variant="success")                        
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