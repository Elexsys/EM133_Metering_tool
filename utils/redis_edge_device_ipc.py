#!/usr/bin/env python3
import json
import redis_custom_library as redis_lib
from datetime import datetime
import os
import numpy as np
import toml
from pubsub_topic_encoder_decoder import PubSubTopicEncoderDecoder as psted
from redis_message_structures import RedisEncoderDecoder

DATE_TIME_STRING = "%m/%d/%Y %H:%M:%S:%f"
CONFIG_FILE = f'{os.path.dirname(__file__)}/../config/config_python_modules.toml'

class Redis_edge_device_ipc():
    def __init__(self, device_name, device_id):
        self.config = toml.load(CONFIG_FILE)
        self._redis_server = redis_lib.connect_to_redis_server()
        
        # Create subscriber and subscribe to requred channels
        self.subscriber = self._redis_server.pubsub()
        self.subscriber.psubscribe('error-master')
        # self.subscriber.psubscribe('trigger-reporting')
        # self.subscriber.psubscribe('group-command')

        # self.command_channel = 'command-' + device_name
        self.command_channel = psted.encode_command_topic(device_name, device_id)
        self.subscriber.psubscribe(self.command_channel)
        print("\'" + device_name + "\' program is receiving commands on channel: \'" + self.command_channel + "\'")  #TODO: ERROR
        self.reporting_frequency = self.config["ipc-parameters"]["reporting_frequency"]


    def publish_data(self, device_name, device_num, reading_type, data, date_time_keys):
        # TODO: hardcoded str->dt transformation for redis_subscriber_db for a single column time
        # print(f"DATA IN redis_edge_device_ipc\n{data}")
        # for key in date_time_keys:
        #     try:
        #         data[key] = data[key].strftime(DATE_TIME_STRING)
        #     except Exception:
        #         pass
        # print(data)
        # data_json = json.dumps(data, indent = 4)
        # print(f"Publishing to {topic}")
        # device_name = f"{device_type}_{device_num}"
        data_json = RedisEncoderDecoder.encode_reading(data)
        readings_topic = psted.encode_readings_topic(device_name, device_num, reading_type)
        # print(f"reading type msg sent === {reading_type}")
        self.send_message(readings_topic, data_json)
        # self._redis_server.publish(readings_topic, data_json)


    def listen(self, handle_command, log_reading, handle_error, set_sleep_time):
        message = self.subscriber.get_message()
        
        while message != None:
            
            if redis_lib.get_pattern(message) is not None:

                channel = redis_lib.get_channel(message)
                
                # If message from 'error-master' channel then handle the error
                if channel == 'error-master':
                    handle_error(redis_lib.get_data(message))

                # Handle commands sent through the command channel
                elif channel == self.command_channel:
                    handle_command(redis_lib.get_data(message))
            
            message = self.subscriber.get_message()
            #TODO: add an emergency heart beat, incase taking ages
            

    def send_message(self, channel, data):
        # print("Sending: " + channel + ", " + data) #TODO: ERROR
        # if 'statcom' in channel and 'basic' in channel: print(f"statcom published: {json.loads(data)['time']}")
        self._redis_server.publish(channel, data)
        
        
        
    #     def __init__(
    #     self, 
    #     time: datetime, 
    #     task_name: str, 
    #     task: types.FunctionType
    # ) -> None:
    #     self.time = time
    #     self.task_name = task_name
    #     self.task = task
    #     self.done = False
    
    # def execute_task():
    #     self.task