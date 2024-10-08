from typing import List, Dict
import pathlib
import yaml
import json
import arrow
from hashlib import sha256
from datetime import datetime
import pytz
from jesselivecli.config import get_default_config  # Import the default timezone

def load_config(config_filename: str) -> Dict:
    str_filename = str(config_filename)
    cfg_file = pathlib.Path(config_filename)
    if not cfg_file.is_file():
        print(f"{cfg_file} not found")
        return None  # Return None if the file is not found

    try:
        with open(cfg_file, "r") as file:
            if str_filename.endswith(('.yml', '.yaml')):
                return yaml.load(file, yaml.SafeLoader)
            elif str_filename.endswith('.json'):
                return json.load(file)
            else:
                print(f"Unsupported file extension for {cfg_file}")
                return None
    except (yaml.YAMLError, json.JSONDecodeError) as e:
        print(f"Error loading configuration file {cfg_file}: {e}")
        return None  # Return None if there's an error loading the file

def generate_ws_url(host: str, port: str, password: str) -> str:
    hashed_local_pass = sha256(password.encode('utf-8')).hexdigest()
    return f"ws://{host}:{port}/ws?token={hashed_local_pass}"    
            
def timestamp_to_date(timestamp: int, timezone: str = None) -> str:
    """Convert a timestamp to a formatted date string in the specified timezone."""
    if timezone is None:
        timezone = get_default_config()['DEFAULT_TIMEZONE']
    # Check if the timestamp is in milliseconds and convert to seconds
    timestamp = int(timestamp) / 1000
    
    # Convert the timestamp to a datetime object
    dt = datetime.utcfromtimestamp(timestamp).replace(tzinfo=pytz.utc)
    
    # Convert the datetime to the specified timezone
    target_timezone = pytz.timezone(timezone)
    dt = dt.astimezone(target_timezone)
    
    # Format the datetime as a string
    return dt.strftime('%Y-%m-%d %H:%M:%S %Z%z')