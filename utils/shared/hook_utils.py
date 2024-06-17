import json
import subprocess
import logging
import sys
import shutil
import time
import netifaces

def get_mac_of_first_ethernet():
    """
    Get MAC address of first ethernet card
    """
    interfaces = netifaces.interfaces()
    for interface in interfaces:
        if interface.startswith("e"):
            info = netifaces.ifaddresses(interface)[netifaces.AF_LINK]
            if info and info[0] and info[0]["addr"]:
                mac_address = info[0]["addr"]
                logging.info(f"Found MAC address {mac_address} of interface {interface}")
                return mac_address
    return None

def get_mac_of_first_ethernet_failsafe():
    """
    Get MAC address of first ethernet card with retries, if no success return empty string
    """
    for iteration in range(3): # number of tries to get MAC addrees of first NIC
        mac_address = get_mac_of_first_ethernet()
        if mac_address:
            return mac_address
        time.sleep(5) # delay in seconds between tries in case when list of interfaces is empty
        logging.info(f"Make {iteration} attempt to get MAC address of first ethernet card")
    return ""

def translate_config(obj, translation_func):
    """
    Recursively translates configuration keys using the provided translation function.
    """
    if isinstance(obj, dict):
        return {translation_func(k): translate_config(v, translation_func) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [translate_config(i, translation_func) for i in obj]
    else:
        return obj

def translate_config_coda_to_snap(obj):
    """
    Translates configuration keys from coda style (underscore) to snap style (dash).
    """
    return translate_config(obj, lambda k: k.replace("_", "-"))

def translate_config_snap_to_coda(obj):
    """
    Translates configuration keys from snap style (dash) to coda style (underscore).
    """
    return translate_config(obj, lambda k: k.replace("-", "_"))

def snapctl_get(key):
    """
    Gets a snap configuration key using snapctl.
    """
    try:
        result = subprocess.run(["snapctl", "get", key], capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to get snap configuration for key: {key}: {e}")
        sys.exit(1)

def snapctl_set(key, json_data):
    """
    Sets a snap configuration key to the provided JSON data using snapctl.
    """
    json_str = json.dumps(json_data)
    logging.debug(f"Setting {key} to {json_data}")
    try:
        subprocess.run(["snapctl", "set", f"{key}={json_str}"], check=True)
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to set {key}: {e}")
        sys.exit(1)

def load_json(file_path):
    """
    Loads and returns the JSON data from the specified file.
    """
    try:
        with open(file_path, "r") as f:
            logging.debug(f"Loading {file_path}")
            content = json.load(f)
            logging.debug(f"Loaded content: {content}")
            return content
    except (IOError, json.JSONDecodeError) as e:
        logging.error(f"Failed to load or parse {file_path}: {e}")
        sys.exit(1)

def save_json(path, data):
    """
    Saves the provided JSON data to the specified file path.
    """
    logging.debug(f"Writing configuration to {path}")
    try:
        with open(path, "w") as f:
            json_str = json.dumps(data, indent=4)
            logging.debug(f"Configuration data: {json_str}")
            f.write(json_str)
            logging.info(f"Data saved to {path}")
    except IOError as e:
        logging.error(f"Failed to save data to {path}: {e}")
        sys.exit(1)

def copy_configuration_files(src_dir, dst_dir):
    """
    Copies configuration files from source directory to destination directory.
    """
    try:
        shutil.copytree(src_dir, dst_dir)
        logging.info(f"Copied configuration files from {src_dir} to {dst_dir}")
    except shutil.Error as e:
        logging.error(f"Failed to copy configuration files: {e}")
        sys.exit(1)