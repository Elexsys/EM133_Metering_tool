#!/usr/bin/env python3
import json
from datetime import datetime, timezone
import os
import numpy as np
import toml

import redis_custom_library as redis_lib
from pubsub_topic_encoder_decoder import PubSubTopicEncoderDecoder as psted
from redis_message_structures import RedisEncoderDecoder


CONFIG_FILE =  f'{os.path.dirname(__file__)}/../config/config_python_modules.toml'

class RedisStateAggregatorIpc():
    def __init__(self, file_path: str):
        self._caller_path = file_path
        self.config = toml.load(CONFIG_FILE)
        self._redis_server = redis_lib.connect_to_redis_server()
        self._redis_pubsub = self._redis_server.pubsub(ignore_subscribe_messages=True)
        self._redis_pubsub.psubscribe(psted.get_state_answer_pattern(file_path=file_path))


    def ask_query(self, query: str):
        self.publish_query(query=query)
        # print("\n\nHELLO WORR\n\n")
        result = self.receive_response()
        return result
        
        
    def publish_query(self, query: str):
        msg = {
            "datetime": datetime.now(tz=timezone.utc),
            "query": query
            }
        encoded_msg = RedisEncoderDecoder.encode_json_with_date(raw_data=msg)
        self._redis_server.publish(
            channel=psted.encode_state_query_topic(file_path=self._caller_path),
            message=encoded_msg)
        
        
    def receive_response(self):
        # print("A")
        msg: dict = redis_lib.get_next_message(subscriber=self._redis_pubsub, blocking=True)
        # print("B")
        msg = redis_lib.get_data(message=msg)
        msg = RedisEncoderDecoder.decode_json_with_date(json_data=msg)
        return msg