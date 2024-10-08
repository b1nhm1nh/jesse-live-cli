# config.py
import os
# Define the default timezone for the application
DEFAULT_CONFIG = None

def get_default_config():
    global DEFAULT_CONFIG
    if DEFAULT_CONFIG is None:
        DEFAULT_CONFIG = {
            'DEFAULT_TIMEZONE': os.getenv('DEFAULT_TIMEZONE', 'ASIA/BANGKOK'),
            'DEFAULT_SERVER_CONFIG': os.getenv('DEFAULT_SERVER_CONFIG', 'server.json'),
            'DEFAULT_EXCHANGE': os.getenv('DEFAULT_EXCHANGE', 'Binance Perpetual Futures'),
            'DEFAULT_EXCHANGE_API_KEY_ID': os.getenv('DEFAULT_EXCHANGE_API_KEY_ID', 'exchange_api_key_id'),
            'DEFAULT_NOTIFICATION_API_KEY_ID': os.getenv('DEFAULT_NOTIFICATION_API_KEY_ID', 'notification_api_key_id')
        }
    return DEFAULT_CONFIG

