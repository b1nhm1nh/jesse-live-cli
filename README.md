# jesse-live-cli
Jesse Live Addon, control Jesse GUI from terminal

Warning: This is a hack version on Jesse, use it as your own risk.

This version compatible with Jesse v1.2.*
### Installing 

clone this repo [https://github.com/b1nhm1nh/jesse-live-cli.git]
run 
```
git clone https://github.com/b1nhm1nh/jesse-live-cli.git
cd jesse-live-cli
pip3 install -e .
```

config timezone in config.py
```
# Define the default timezone for the application
DEFAULT_TIMEZONE = 'ASIA/BANGKOK'
```


### Create config files
Make a folder for jesse-cli, it can be a seperate folder from Jesse-bot project.
```
fool jesse lib by:
make a .env file
mkdir storage
mkdir strategies
```
Create a `server.yml` file in the root directory,

```yaml
refer to server.example.yml & server.example.json
---

```


Create a `routes.yml` file in the root directory:

```yaml
refer to routes.example.yml & routes.example.json
```

Jesse-live-cli will loads `server.yml` and `routers.yml` on default, we can specify config files with `--server_config`, `--routes_config`  options

```
jesse-live-cli start --server_config server.json --routes_config routes.json

```

### Runing

Start Jesse
```
jesse run
```

Start a Websocket proxy server: Make a websocket proxy in front of Jesse port. You should modify your server config to connect to proxy port. jesse-live-cli still can connect to Jesse directly

```
jesse-live-cli proxy --listen_port
```
Config routes & server config, connect to Websocket proxy port above

Start a CLI view of Jesse 
```
jesse-live-cli run 
```

Start Live mode based on `routes` config
```
jesse-live-cli start
```

Stop Live mode based on `routes` config

```
jesse-live-cli stop
```

Restart Live mode based on `routes` config

```
jesse-live-cli restart
```

### New Features
- cli proxy mode: a websocket proxy in front of Jesse to forward data to all connected clients, with auto reconnect 
- Session Management: Switch between multiple sessions using number keys (1-9).
- Log Viewer: View logs
- Route Management: Display and manage routes. Stop / Start Live session it not implemented 

### Limitation & known bugs
 - Jesse can run multiple Live session when using: `jesse-live-cli run`.
 - Multi sessions of Jesse Live Cli can connect to Jesse, including Jesse web, but only the last one will receive data. You should use `jesse-live-cli proxy --listen_port` if you want to multiple Live sessions concurrently.

### Todo:
- Save sessions into files.
- Start / Stop session from UI.
