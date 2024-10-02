# jesse-live-cli
Jesse Live Addon, control Jesse GUI from terminal

Warning: This is a hack version on Jesse, use it as your own risk.

### Installing 

clone this repo [https://github.com/b1nhm1nh/jesse-live-cli.git]
run 
```
git clone https://github.com/b1nhm1nh/jesse-live-cli.git
cd jesse-live-cli
pip3 install -e .
```

### Create config files
Make a folder for jesse-cli, it can be a seperate folder of Jesse project.

Create a `server.yml` file in the root directory,

```yaml
---
server:
  host: 'localhost'
  port: 9000
  password: 'test'
config:
  logging:
    order_cancellation: true
    position_opened: true
    position_reduced: true
    position_closed: true
    order_execution: true
    order_submission: true
    trading_candles: true
    balance_update: true
    position_increased: true
    shorter_period_candles: false
  exchanges:
    Binance Perpetual Futures Testnet:
      futures_leverage: '10'
      name: Binance Perpetual Futures Testnet
      balance: 1000
      settlement_currency: USDT
      futures_leverage_mode: cross
      fee: 0.006
    Binance Perpetual Futures:
      futures_leverage: '10'
      name: Binance Perpetual Futures
      balance: 1000
      settlement_currency: USDT
      futures_leverage_mode: cross
      fee: 0.006
    Bybit USDT Perpetual:
      futures_leverage: 2
      name: Bybit USDT Perpetual
      balance: 10000
      settlement_currency: USDT
      futures_leverage_mode: cross
      fee: 0.001
    Bitget USDT Perpetual:
      futures_leverage: 2
      name: Bitget USDT Perpetual
      balance: 10000
      futures_leverage_mode: cross
      fee: 0.0006
    Binance Spot:
      futures_leverage: 2
      name: Binance Spot
      balance: 10000
      settlement_currency: USDT
      futures_leverage_mode: cross
      fee: 0.001
    Bybit USDT Perpetual Testnet:
      futures_leverage: 2
      name: Bybit USDT Perpetual Testnet
      balance: 10000
      settlement_currency: USDT
      futures_leverage_mode: cross
      fee: 0.001
    Binance US Spot:
      futures_leverage: 2
      name: Binance US Spot
      balance: 10000
      settlement_currency: USDT
      futures_leverage_mode: cross
      fee: 0.001
  persistency: true
  notifications:
    enabled: true
    position_report_timeframe: 1h
    events:
      executed_orders: true
      errors: true
      submitted_orders: false
      terminated_session: true
      started_session: true
      opened_position: true
      cancelled_orders: false
      updated_position: true
  warm_up_candles: 200
  generate_candles_from_1m: false
debug_mode: true
paper_mode: true
```


Create a `routes.yml` file in the root directory:

```yaml
routes:
- exchange: Binance Perpetual Futures
  symbol: ETH-USDT
  timeframe: 1m
  strategy: ExampleStrategy
- exchange: Binance Perpetual Futures
  symbol: BNB-USDT
  timeframe: 1m
  strategy: ExampleStrategy
extra_routes:
- exchange: Binance Perpetual Futures
  symbol: ETH-USDT
  timeframe: 5m
- exchange: Binance Perpetual Futures
  symbol: ETH-USDT
  timeframe: 15m
- exchange: Binance Perpetual Futures
  symbol: ETH-USDT
  timeframe: 30m
- exchange: Binance Perpetual Futures
  symbol: BNB-USDT
  timeframe: 5m
- exchange: Binance Perpetual Futures
  symbol: BNB-USDT
  timeframe: 15m
- exchange: Binance Perpetual Futures
  symbol: BNB-USDT
  timeframe: 30m  
```

Jesse-live-cli will loads `server.yml` and `routers.yml` on default, we can specify config files with `--server_yaml`, `--server_json`, `--routes_yaml`, `--routes_json` options

```
jesse-live-cli start --server_json server.json --routes_json routes.json

```

### Runing

Start Jesse
```
jesse run
```

Start a Websocket proxy server first
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


### Limitation & known bugs
 - Jesse can run multiple Live session when using: `jesse-live-cli start`.
 - Multi sessions of Jesse Live Cli can connect to Jesse, including Jesse web, but only the last one will receive data.
