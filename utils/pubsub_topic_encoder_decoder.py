#!/usr/bin/env python3
"""
Contains encoders and decoders for the pubsub topic using naming conventions
suggested by both google cloud and hivemq 
https://cloud.google.com/pubsub/docs/admin
https://www.hivemq.com/blog/mqtt-essentials-part-5-mqtt-topics-best-practices/
"""

class PubSubTopicEncoderDecoder():
    def __init__(self) -> None:
        pass

    @staticmethod
    def encode_command_topic(device_name, device_num):
        return f"device/{device_name}/{device_num}/command"

    @staticmethod
    def decode_command_topic(topic):
        topic = topic.split("/")
        device_name = topic[1]
        device_num  = topic[2]
        return {
            "device_name": device_name,
            "device_num": device_num
        }

    @staticmethod
    def encode_group_command_topic(device_type):
        return f"device/{device_type}/group_command"

    @staticmethod
    def decode_group_command_topic(topic):
        topic = topic.split("/")
        device_name = topic[1]
        return {
            "device_name": device_name
        }
        
    @staticmethod
    def get_group_command_pattern():
        return "device/*/group_command"
        
    @staticmethod
    def encode_user_command_topic() -> str:
        return "user_command"
    
    @staticmethod
    def decode_user_command_topic() -> str:
        raise NotImplementedError

    @staticmethod
    def encode_readings_topic(
        device_name: str, 
        device_num: int, 
        reading_type: str
    ) -> str:
        return f"device/{device_name}/{device_num}/readings/{reading_type}"
    
    @staticmethod
    def get_readings_topic_pattern() -> str:
        return "device/*/*/readings/*"

    @staticmethod
    def decode_readings_topic(topic):
        # print(topic)
        topic = topic.split("/")
        device_name = topic[1]
        device_num = topic[2]
        try:
            reading_type = topic[4]
        except Exception as e:
            print(f"topic decode failed: {topic}: {e}")
            
        return {
            "device_name": device_name,
            "device_num": device_num,
            "reading_type": reading_type,
        }

    @staticmethod
    def encode_combined_readings_topic() -> str:
        return "combined_readings"

    @staticmethod
    def decode_combined_readings_topic(topic):
        raise NotImplementedError

    @staticmethod
    def encode_heartbeat(module_name, module_num=None):
        return f"heartbeat/{module_name}/{module_num}"

    @staticmethod
    def decode_heartbeat(topic):
        topic = topic.split("/")
        module_name = topic[1]
        module_num = topic[2]
        return {
            "module_name": module_name,
            "module_num": module_num
        }

    @staticmethod
    def encode_error_topic(module):
        return f"device/{module}/errors"

    @staticmethod
    def decode_error_topic(topic):
        topic = topic.split("/")
        module_name = topic[1]
        return {
            'module_name': module_name
        }
        
    @staticmethod
    def encode_power_command_topic():
        return "power_command"
    
    @staticmethod
    def decode_power_command_topic():
        raise NotImplementedError
    
    @staticmethod
    def get_power_command_pattern():
        return "power_command"
    
        
    # EVES
    @staticmethod
    def encode_system_status_topic():
        return "system_status"

    # SiteStateStorage channels
    
    @staticmethod
    def encode_site_storage_listener(file_path: str):
        file_name = file_path.rsplit('/', 1)[-1].split('.')[0]
        return f"site_storage_listener/{file_name}"
    
    @staticmethod
    def get_site_storage_listener_pattern():
        return "site_storage_listener/*"
    
    
    @staticmethod
    def encode_state_query_topic(file_path: str) -> str:
        sender_program = file_path.rsplit('/', 1)[-1].split('.')[0]
        return f"state/query/{sender_program}"
    
    @staticmethod
    def decode_state_query_topic(topic: str) -> dict:
        topic_info: list = topic.split('/')
        sender_program: str = topic_info[2]
        return {"sender_program": sender_program}
    
    @staticmethod
    def get_state_query_topic_pattern() -> str:
        return "state/query/*"
    
    @staticmethod
    def encode_state_answer_topic(receiving_program: str) -> str:
        return f"state/answer/{receiving_program}"

    @staticmethod
    def decode_state_answer_topic(topic: str) -> dict:
        topic_info: list = topic.split('/')
        sender_program: str = topic_info[2]
        return {"sender_program": sender_program}

    @staticmethod
    def get_state_answer_pattern(file_path: str):
        sender_program = file_path.rsplit('/', 1)[-1].split('.')[0]
        return f"state/answer/{sender_program}"
    


class MqttTopicEncoderDecoder():
    def __init__(self) -> None:
        pass

    @staticmethod
    def encode_config_channel(site_id):
        return f"site/{site_id}/config/None"
    
    @staticmethod
    def encode_sync_postgres_channel(site_id):
        return f"site/{site_id}/data/None"
    
    @staticmethod
    def decode_channel(topic):
        topic = topic.split("/", 3)
        site_id = topic[1]
        command = topic[2]
        metadata = topic[3]
        return {
            "site_id": site_id,
            "command": command,
            "metadata": metadata
        }
    
    @staticmethod
    def encode_heartbeat():
        pass
    
    @staticmethod
    def decode_heartbeat():
        pass
    