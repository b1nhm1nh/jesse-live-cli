from typing import List, Dict
import pathlib
import yaml
import json
from hashlib import sha256

def get_config(config_filename: str) -> Dict:
    cfg_file = pathlib.Path(config_filename)
    if not cfg_file.is_file():
        print(f"{config_filename} not found")
        return None  # Return None if the file is not found
    else:
        with open(config_filename, "r") as ymlfile:
            try:
                cfg = yaml.load(ymlfile, yaml.SafeLoader)
                return cfg
            except yaml.YAMLError as e:
                print(f"Error loading YAML file {config_filename}: {e}")
                return None  # Return None if there's an error loading the file

def get_config_json(config_filename: str) -> Dict:
    cfg_file = pathlib.Path(config_filename)
    if not cfg_file.is_file():
        print(f"{config_filename} not found")
        return None  # Return None if the file is not found
    else:
        with open(config_filename, "r") as jsonfile:
            try:
                cfg = json.load(jsonfile)
                return cfg
            except json.JSONDecodeError as e:
                print(f"Error loading JSON file {config_filename}: {e}")
                return None  # Return None if there's an error loading the file
            
            
def generate_ws_url(host: str, port: str, password: str) -> str:
    hashed_local_pass = sha256(password.encode('utf-8')).hexdigest()
    return f"ws://{host}:{port}/ws?token={hashed_local_pass}"    
            