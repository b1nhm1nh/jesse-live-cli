from typing import List, Dict
import pathlib
import yaml
import json
import arrow
from hashlib import sha256

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
            
def timestamp_to_date(timestamp) -> str:
    if timestamp is None:
        return ''
    if type(timestamp) == str:
        timestamp = int(timestamp)

    return str(arrow.get(timestamp))