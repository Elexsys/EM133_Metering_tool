#!/usr/bin/env python3
import redis
import os
import time
import sys
import toml
import json
from datetime import datetime, timezone

CONFIG_FILE_PATH = f'{os.path.dirname(__file__)}/../config/config_python_modules.toml'

CONFIG_FILE = toml.load(CONFIG_FILE_PATH)
REDIS_SERVER_DB = CONFIG_FILE["redis"]["db"] # os.getenv('REDIS_DB')
IP_ADDRESS = CONFIG_FILE["redis"]["host"]
REDIS_SERVER_PORT = CONFIG_FILE["redis"]["port"]

def connect_to_redis_server() -> redis.Redis:
    try:
        r = redis.Redis(host=IP_ADDRESS, port=REDIS_SERVER_PORT, db=REDIS_SERVER_DB)
        return r
    except (redis.exceptions.ConnectionError) as e:
        print(f"Error connecting to Redis server: {e}") #TODO: ERROR
        # print(f"Attemping to start-up server...") #TODO: ERROR
        # logger.warning(f"CONNECTION FAILURE: Error connecting to Redis server: {e}\n"
                        # "Attemping to start-up server...")

        try:
            # Executes "redis_server" on the linux host
            os.system("redis-server")
            time.sleep(3)
            r = redis.Redis(host=IP_ADDRESS, port=REDIS_SERVER_PORT, db=REDIS_SERVER_DB)
            # print("Redis server successfully started and connected to.") #TODO: ERROR
            # logger.info("REDIS: Redis server successfully started and connected to.")
            return r
        
        except (redis.exceptions.ConnectionError) as e:
            # print(f"Redis server still unable to be connected to. System exiting.") #TODO: ERROR
            # logger.error("REDIS: Redis server still unable to be connected to. System exiting.")
            sys.exit(1)
            
            
def get_next_message(subscriber, blocking: bool=False) -> dict:
    """ Returns the next message in the subscribers queue. None if there is no 
    meessage 
    """
    while True:
        time.sleep(0.001)
        message = subscriber.get_message()
        if message is None or 'message' not in message["type"]:
            if blocking == False:
                return None
            else:
                continue
        else:
            return message
    

def get_current_message(subscriber, blocking: bool=False) -> dict:
    """ Returns the next message in the queue that has a timestamp >= time 
    when this method was called. 
    """
    # message = subscriber.get_message()
    # if message is None or message["pattern"] is None:
    now = datetime.now(tz=timezone.utc)
    last_msg = None
    while True:
        time.sleep(0.01)
        msg = get_next_message(subscriber=subscriber, blocking=blocking)
        
        if msg is None:
            # print("None msg leaving")
            return last_msg
        
        data = json.loads(get_data(msg))
        
        if datetime.fromisoformat(data["datetime"]) >= now:
            # if "battery" in get_channel(msg):
            #     print(f"\nCurrent msg leaving {get_channel(msg)}\n")
            return msg
        else:
            # if "battery" in get_channel(msg):
            # print(f"Check next message from {get_channel(msg)}")
            last_msg = msg
        

def get_pattern(message):
    if message is not None and message["pattern"] is not None:
        return message["pattern"].decode("utf-8")
    return None

def get_channel(message):
    if message is not None and message["pattern"] is not None:
        return message["channel"].decode("utf-8")
    return None

def get_data(message):
    if message is not None and message["pattern"] is not None:
        return message["data"].decode("utf-8")
    return None
