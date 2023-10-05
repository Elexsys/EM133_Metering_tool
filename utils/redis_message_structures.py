#!/usr/bin/env python3
import json
from datetime import datetime, timezone

class CommandMessage:
    def __init__(
        self, 
        sender_program_name: str, 
        recipient_device_name: str, 
        command_key_word: str, 
        settings: str, 
        datetime: datetime=datetime.now(tz=timezone.utc)
    ) -> None:
        self.datetime = datetime
        self.sender_program_name = sender_program_name
        self.recipient_device_name = recipient_device_name
        self.command_key_word = command_key_word
        self.settings = settings
    
    def encode(self) -> dict:
        return self.__dict__
        
    @staticmethod
    def decode(data: dict):
        return CommandMessage(
            datetime=data["datetime"],
            sender_program_name=data["sender_program_name"],
            recipient_device_name=data["recipient_device_name"],
            command_key_word=data["command_key_word"],
            settings=data["settings"]
        )
    

# DATE_TIME_STRING = "%m/%d/%Y %H:%M:%S:%f"

class RedisEncoderDecoder(object):
    @staticmethod
    def encode_command(command_message: CommandMessage):
        command_data = command_message.__dict__
        command_data["datetime"] = command_data["datetime"].isoformat()
        return json.dumps(command_data)

    def encode_command_for_database(command_dict_original):
        command_dict = command_dict_original.copy()
        command_dict["settings"] = ",".join(list(map(lambda x: str(x), command_dict["settings"])))
        return command_dict

    @staticmethod
    def decode_command(json_data) -> CommandMessage:
        if type(json_data) == str:
            command_data = json.loads(json_data)
            command_data["datetime"] = datetime.fromisoformat(command_data["datetime"])
        else:
            command_data = json_data
            
        return CommandMessage(
            datetime=command_data["datetime"], 
            sender_program_name=command_data["sender_program_name"], 
            recipient_device_name=command_data["recipient_device_name"], 
            command_key_word=command_data["command_key_word"], 
            settings=command_data["settings"]
            )

    @staticmethod
    def encode_reading(reading_dict_original):
        reading_dict = reading_dict_original.copy()
        # reading_dict["time"] = reading_dict["time"].strftime(DATE_TIME_STRING)
        reading_dict["datetime"] = reading_dict["datetime"].isoformat()
        return json.dumps(reading_dict)
        
    @staticmethod
    def decode_reading(json_data) -> dict:
        readings_data = json.loads(json_data)
        # readings_data["time"] = datetime.strptime(readings_data["time"], DATE_TIME_STRING)
        readings_data["datetime"] = datetime.fromisoformat(readings_data["datetime"])
        return readings_data

    @staticmethod
    def encode_combined_reading(combined_readings_dict_original):
        combined_readings_dict = combined_readings_dict_original.copy()
        
        # combined_readings_dict["time"] = combined_readings_dict["time"].strftime(DATE_TIME_STRING)
        combined_readings_dict["datetime"] = combined_readings_dict["datetime"].isoformat()

        for key in combined_readings_dict.keys():
            if key != "datetime":
                combined_readings_dict[key] = RedisEncoderDecoder.encode_reading(combined_readings_dict[key])
        
        return json.dumps(combined_readings_dict)
    
    @staticmethod
    def decode_combined_reading(json_data):
        combined_readings_dict = json.loads(json_data)

        # combined_readings_dict["time"] = datetime.strptime(combined_readings_dict["time"], DATE_TIME_STRING)
        combined_readings_dict["datetime"] = datetime.fromisoformat(combined_readings_dict["datetime"])

        for key in combined_readings_dict.keys():
            if key != "datetime":
                combined_readings_dict[key] = RedisEncoderDecoder.decode_reading(combined_readings_dict[key])
        
        return combined_readings_dict

    @staticmethod
    def encode_subprocess_log_for_database(process_connection, starting_flag):
        subprocess_log = {}
        
        subprocess_log["datetime"] = datetime.now(tz=timezone.utc)
        subprocess_log["subprocess_process_name"] = process_connection.module_name
        subprocess_log["subprocess_pid"] = process_connection.process_id
        subprocess_log["starting_or_killing"] = starting_flag
        subprocess_log["arguments"] = ','.join(list(map(lambda x: str(x), process_connection.args)))
        return subprocess_log

    @staticmethod
    def decode_subprocess_log(json_data):
        subprocess_log = json.loads(json_data)
        # subprocess_log["time"] = datetime.strptime(subprocess_log["time"], DATE_TIME_STRING)
        subprocess_log["datetime"] = datetime.fromisoformat(subprocess_log["datetime"])
        return subprocess_log

    @staticmethod
    def encode_raspi_state_database(raspi_state):
        # raspi_state["time"] = raspi_state["time"].strftime(DATE_TIME_STRING)
        raspi_state["datetime"] = raspi_state["datetime"].isoformat()
        return json.dumps(raspi_state)
    
    @staticmethod
    def decode_raspi_state_database(raspi_state_json):
        raspi_state = json.loads(raspi_state_json)
        raspi_state["datetime"] = datetime.fromisoformat(raspi_state["datetime"])
        return raspi_state

    @staticmethod
    def encode_error_code(error_code):
        # error_code["time"] = error_code["time"].strftime(DATE_TIME_STRING)
        error_code["datetime"] = error_code["datetime"].isoformat()
        return json.dumps(error_code)

    @staticmethod
    def decode_error_code(error_code_json):
        error_code_json = json.loads(error_code_json)
        # error_code_json['time'] = datetime.strptime(error_code_json['time'], DATE_TIME_STRING)
        error_code_json['datetime'] = datetime.fromisoformat(error_code_json['datetime'])
        return error_code_json
    
    @staticmethod
    def encode_json_with_date(raw_data: dict):
        raw_data = raw_data.copy()
        if "datetime" in raw_data.keys():
            raw_data["datetime"] = raw_data["datetime"].isoformat()
        else:
            raw_data["datetime"] = datetime.now(tz=timezone.utc).isoformat()
            
        return json.dumps(raw_data)

    @staticmethod
    def decode_json_with_date(json_data):
        json_data = json.loads(json_data)
        json_data['datetime'] = datetime.fromisoformat(json_data['datetime'])
        return json_data
