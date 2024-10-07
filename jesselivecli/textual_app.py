import asyncio
import json
import websockets
from typing import Optional

from textual.app import App
from textual.widgets import Button, Label
from textual.reactive import reactive

class JesseCliApp(App):
    CSS_PATH = "app.css"

    websocket: Optional[websockets.WebSocketClientProtocol] = None
    websocket_task = None
    command_queue = asyncio.Queue()
    messages = reactive(None)
    id_list = reactive([])
    default_id = ""
    

    def compose(self):
        yield Button("Send Command", id="send_command")
        yield Label("bot State", id="bot_state")
        yield Label("Log", id="log")

    def on_mount(self):
        self.set_interval(1/60, self.update_bot_state)

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "send_command":
            asyncio.create_task(self.send_command({"command": "example_command"}))

    async def send_command(self, command):
        await self.command_queue.put(command)

    async def handle_message(self, message):
        # Process incoming messages and update bot state
        self.messages = message  # Assuming message contains bot state
        data = json.loads(message)
        id = data['id']
        if self.default_id == "":
            self.default_id = id
        if id not in self.id_list:
            self.id_list.append(id)

        event_info = data['event'].split(".")
        event = event_info[1] if len(event_info) == 2 else ""
        event_trading_mode = event_info[0] if len(event_info) == 2 else ""

        # if id != self.default_id:
        #     return
        if event == 'info_log':
            self.handle_info_log(data)        
        elif event == 'general_info':
            self.handle_info_log(data['data'])
            # self.routes = self.infos['routes']

    def handle_info_log(self, data):
        self.query_one("#log").update(f"Bot log: {data}")

    def update_bot_state(self):
        if self.messages:
            self.query_one("#bot_state").update(f"Bot State: {self.messages}")

    async def on_load(self):
        await self.start_client()

    async def start_client(self):
        self.websocket_task = asyncio.create_task(client(self, "SessionName"))

async def consumer_handler(websocket, app):
    async for message in websocket:
        # print(f"Received message: {message}")
        # response = json.loads(message)
        await app.handle_message(message)

async def producer_handler(websocket, app, name):
    await websocket.send(json.dumps({"command": "join", "args": {"name": name}}))
    while True:
        command = await app.command_queue.get()
        await websocket.send(json.dumps(command))
        app.command_queue.task_done()

async def client(app, name):
    uri = "ws://localhost:9009"

    async with websockets.connect(uri) as websocket:
        app.websocket = websocket
        consumer_task = asyncio.create_task(consumer_handler(websocket, app))
        producer_task = asyncio.create_task(producer_handler(websocket, app, name))
        done, pending = await asyncio.wait(
            [consumer_task, producer_task],
            return_when=asyncio.FIRST_COMPLETED,
        )
        for task in pending:
            task.cancel()

if __name__ == "__main__":
    app = JesseCliApp()
    app.run()
