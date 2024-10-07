from typing import List, Dict
import pathlib
import yaml
import json
import arrow
from hashlib import sha256
from datetime import datetime
import pytz

def load_config(config_filename: str) -> Dict:
    cfg_file = pathlib.Path(config_filename)
    if not cfg_file.is_file():
        print(f"{config_filename} not found")
        return None  # Return None if the file is not found

    try:
        with open(config_filename, "r") as file:
            if config_filename.endswith(('.yml', '.yaml')):
                return yaml.load(file, yaml.SafeLoader)
            elif config_filename.endswith('.json'):
                return json.load(file)
            else:
                print(f"Unsupported file extension for {config_filename}")
                return None
    except (yaml.YAMLError, json.JSONDecodeError) as e:
        print(f"Error loading configuration file {config_filename}: {e}")
        return None  # Return None if there's an error loading the file

def generate_ws_url(host: str, port: str, password: str) -> str:
    hashed_local_pass = sha256(password.encode('utf-8')).hexdigest()
    return f"ws://{host}:{port}/ws?token={hashed_local_pass}"    
            
def timestamp_to_date(timestamp: int, timezone: str = 'ASIA/BANGKOK') -> str:
    """Convert a timestamp to a formatted date string in the specified timezone."""
    # Check if the timestamp is in milliseconds and convert to seconds
    # if timestamp > 1e10:  # Roughly corresponds to a date in 2286
    timestamp = int(timestamp) / 1000
    
    # Convert the timestamp to a datetime object
    dt = datetime.utcfromtimestamp(timestamp).replace(tzinfo=pytz.utc)
    
    # Convert the datetime to the specified timezone
    target_timezone = pytz.timezone(timezone)
    dt = dt.astimezone(target_timezone)
    
    # Format the datetime as a string
    return dt.strftime('%Y-%m-%d %H:%M:%S %Z%z')