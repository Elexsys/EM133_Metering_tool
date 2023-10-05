#!/usr/bin/env python3
import time
from datetime import datetime, timezone
import struct
import sys
import re
import numpy as np
import logging
import toml
import os
import ipaddress

from utils_custom import Utils
import db_logger
from pymodbus.client import ModbusTcpClient
from redis_edge_device_ipc import Redis_edge_device_ipc
from pubsub_topic_encoder_decoder import PubSubTopicEncoderDecoder as psted

# Use either real getmac library for raspios or temporary copied one for buildroot 
from getmac import get_mac_address
# get_mac_address = Utils.get_mac_address

ALLOWED_ATTEMPTS = 3
LOGGER_LEVEL = logging.INFO

logger_setup = db_logger.DBLogger(os.path.basename(__file__), LOGGER_LEVEL)
logger = logger_setup.get_logger()
CONFIG_FILE = f'{os.path.dirname(__file__)}/../config/config_python_modules.toml'

class Edge_device():
    def __init__(
        self, 
        module_name: str, 
        host: ipaddress.IPv4Address, 
        port: int, 
        unit_id: int, 
        uses_modbus: bool
    ) -> None:
        
        # Get mac address from ip
        self.set_device_id(host)

        self.module_name = module_name
        self.module_type = module_name.rsplit("_", 1)[0]
        self.module_num = module_name.rsplit("_", 1)[1]

        if uses_modbus:
            self.host = host
            self.port = port
            self.unit_id = unit_id
            self.client = self.get_new_modbus_client(host, port)
            if not self.check_register_locations():
                error_msg = f"INITIALISE ERROR: registers missing in defined config register blocks for host '{self.host}'. Closing process..."
                print(error_msg) #TODO: ERROR
                logger.info(error_msg)
                sys.exit(1)

        self.state = dict(datetime=None, device_id=None)
        self.redis_connected = False
        try:
            self.redis_ipc = Redis_edge_device_ipc(self.module_name, self.get_module_num())
            self.redis_connected = True
        except:
            print("Failed to connect to redis server... Disabling redis functionality.")

        self.safe_mode = False

        config = toml.load(CONFIG_FILE)
        desired_reporting_frequency = config["ipc-parameters"]["reporting_frequency"]
        min_period = config["min-reporting-periods"][self.module_type]
        self.reporting_period = max(min_period, (1 / desired_reporting_frequency))

        self.slow_reporting_frequency = config["ipc-parameters"]["slow_reporting_frequency"]

        self.time_last_heartbeat = time.time()
        self.heartbeat_frequency = config["global"]['heartbeat_frequency']
        self.heartbeat_topic = psted.encode_heartbeat(
                                module_name=self.module_name,
                                module_num=self.module_num)

        self.set_sleep_time(self.reporting_period)

        self.time_last_publish = time.time()

        # Set reading_type to basic, if another type of reading is done then
        # need to set the state of reading_type e.g. battery basic vs voltage vs
        # temperature
        self.reading_type = "basic"

        self.time_last_command = time.time()
        
        self.state = dict(device_id=self.get_device_id(), datetime=None)

    # getters and setters for child classes
    def get_reporting_period(self):
        return self.reporting_period
    
    def get_slow_reporting_period(self):
        return 1 / self.slow_reporting_frequency
    
    def get_slow_reporting_frequency(self):
        return self.slow_reporting_frequency
    
    def get_module_name(self):
        return self.module_name

    def get_module_type(self):
        return self.module_type
    
    def get_host(self):
        return self.host

    def get_port(self):
        return self.port

    def get_client(self):
        return self.client

    def get_state(self):
        return self.state
    
    def get_unit_id(self):
        return self.unit_id

    def get_device_id(self):
        return self.device_id

    def get_time_last_heartbeat(self):
        return self.time_last_heartbeat

    def get_heartbeat_period(self):
        return 1 / self.heartbeat_frequency

    def get_heartbeat_frequency(self):
        return self.heartbeat_frequency

    def get_reading_type(self):
        return self.reading_type

    def get_module_num(self):
        """
        The number of the device, e.g. 1/3 statcoms installed
        """
        return self.module_num

    def get_heartbeat_topic(self):
        return self.heartbeat_topic

    def get_time_last_command(self):
        return self.time_last_command

    def set_time_last_command(self, time):
        self.time_last_command = time

    def set_time_last_heartbeat(self, time):
        self.time_last_heartbeat = time

    def set_module_name(self, module_name):
        self.module_name = module_name

    def set_reading_type(self, reading_type: str):
        self.reading_type = reading_type

    def reset_state(self):
        self.state = dict(datetime=None, device_id=self.get_device_id())

    def check_safe_mode(self):
        return self.safe_mode

    def turn_on_safe_mode(self):
        self.safe_mode = True
    
    def turn_off_safe_mode(self):
        self.safe_mode = False

    def get_sleep_time(self):
        return self.sleep_time

    def set_sleep_time(self, sleep_time):
        self.sleep_time = sleep_time

    def get_config(self):
        raise NotImplementedError
    
    def get_polarity(self):
        return 1
    
    def get_new_modbus_client(self, host, port):
        return ModbusTcpClient(host=host, port=port)

    def set_device_id(self, host):
        """
        Uses getmac library to return the mac address for an ip
        """
        # Get mac address from ip
        mac = str(get_mac_address(ip=host))
        self.device_id = "".join(mac.split(":"))

    def check_register_locations(self):
        locations = self.get_config_section_and_key_list("basic_read_registers", "location")
        registers_to_read = self.get_config()["basic_read_block"]

        for l in locations:
            found = False
            for block in registers_to_read:
                start = block["start"]
                size = block["size"]

                if start <= l and l <= start + size - 1:
                    found = True
            
            if not found:
                #TODO: ERROR
                # print("ERROR: Register " + str(l) + " not included in register blocks to be bulk read. Check register locations.")
                logger.warning("EDGE DEVICE: Register " + str(l) 
                                + " not included in register blocks to be bulk "
                                + "read. Check register locations.")
                return False
        return True

    def check_double_register(self, dtype):
        if dtype == 'I' or dtype == 'i' or dtype == 'l' or dtype == 'L' or dtype == 'f':
            return True
        else:
            return False

    def check_quadruple_register(self, dtype):
        if dtype == 'q' or dtype == 'Q' or dtype == 'd':
            return True
        else:
            return False

    def sleep(self):
        time.sleep(max(0, self.get_sleep_time()))

    def read_modbus(self, register_blocks):
        """
        https://stackoverflow.com/questions/69881272/pymodbus-read-and-decode-register-value

        Args:
            register_blocks (_type_): _description_

        Returns:
            _type_: _description_
        """
        data_frame = []
        time_stamp = None
        allowed_attempts = ALLOWED_ATTEMPTS

        # TODO refactor below code to remove the large amount of code in a try except block
        for start_register, number_registers in register_blocks:
            read_error = True

            while read_error:
                try:
                    # NOTE register block may need to start at (first_register_addr - 1), some devices may need to
                    # start at the first_register_addr
                    if self.unit_id == None:
                        register_readings = self.client.read_holding_registers(address=start_register, count=number_registers - 1)
                    else:
                        register_readings = self.client.read_holding_registers(address=start_register, count=number_registers - 1, unit=self.unit_id)
                    read_error = False

                    try:
                        register_values = register_readings.registers
                    except Exception as e:
                        print(f"\nError reading modbus reg: {e}\n")
                        raise Exception

                except Exception as e:
                    read_error = True
                    if allowed_attempts > 0:
                        allowed_attempts -= 1
                    else:
                        print(f'{self.get_module_name()} : failed to read {ALLOWED_ATTEMPTS} time. Restarting pymodbus connection.') #TODO: ERROR
                        logger.warning(f"EDGE DEVICE: {self.get_module_name()}: failed to read {ALLOWED_ATTEMPTS} time(s). Restarting pymodbus connection.")
                        self.client = self.get_new_modbus_client(self.host, self.port)

                        allowed_attempts = 3
                    time.sleep(0.5)

            if time_stamp is None:
                time_stamp = time.time()
                
            data_frame.extend(register_values)
        return data_frame
  
    def get_config_section_and_key_list(self, section, key):
        """
        Returns a list of the register data values of the same key from config
        file

        TODO Because offset only exists in the catl battery register config file
        an error is thrown when self.get_config()["offset"] is called for 
        every other device.
        """
        try:
            return list(map(lambda x: x[key], self.get_config()[section]))
        except Exception:
            return list(map(lambda x: 0, self.get_config()[section]))
        # return list(map(lambda x: x[key], self.get_config()[section]))

    def get_map_section_and_key_list(self, given_map, key):
        """
        Returns a list of the register data values of the same key from a given
        dictionary
        """
        return list(map(lambda x: x[key], given_map))

    def get_datetime_values(self):
        return ["datetime"]

    def handle_command(self, command):
        """
        Handles the command sent to the edge device
        """
        raise NotImplementedError

    def listen(self):
        if self.redis_connected:
            self.log_reading()
            self.redis_ipc.listen(
                self.handle_command, 
                self.log_reading, 
                self.handle_error, 
                self.set_sleep_time)

    def handle_error(self, error_code):
        """
        
        """
        if isinstance(error_code, str):
            error_code = int(error_code)

        # add additional logic for which errors to enter into safe mode
        # potentially different degrees of safe mode

        if error_code != 0:
            self.turn_on_safe_mode()
        else:
            self.turn_off_safe_mode()
    
    
    def send_heartbeat(self):
        if self.redis_connected:
            # print("Sending hearbeat from " + self.get_module_name()) #TODO: ERROR
            heartbeat_topic = psted.encode_heartbeat(self.module_name, self.module_num)
            self.redis_ipc.send_message(heartbeat_topic, time.time())
        
        
    # def send_heartbeat_with_wait(self, wait: int):
    #     start: float = time.time()
    #     time_last_heartbeat: float = time.time()
    #     heartbeat_topic = psted.encode_heartbeat(self.module_name, self.module_num)
    #     self.redis_ipc.send_message(heartbeat_topic, time.time())
    #     while time.time() < start + wait:
    #         if time_last_heartbeat + 1/self.heartbeat_frequency < time.time():
    #             self.redis_ipc.send_message(heartbeat_topic, time.time())
    #             self.time_last_heartbeat = time.time()
        

    def log_reading(self):
        """
        Calls the update() method for the edge devices and publishes the data to
        redis. Typically this method is called for each device at the frequency
        specified in the config_python_modules.toml file
        """
        if not self.check_safe_mode():
            # print("Logging") #TODO: ERROR
            self.update()

            if self.state:
                # print(self.state)
                self.publish_data()
        else:
            print("Not logging as in safe mode...")

    def publish_data(self):
        if self.redis_connected:
            # print(f"reading type === {self.get_reading_type()}")
            
            # NOTE only publish the data if the time since last publish is more than
            # 1 sec to avoid the postgres db being spamming with messages
            # if now - self.time_last_publish >= 1:
            device_name = f'{self.module_type}_{self.module_num}'
            self.redis_ipc.publish_data(
                device_name=device_name,
                device_num=self.get_module_num(),
                reading_type=self.get_reading_type(),
                data=self.get_state(),
                date_time_keys=self.get_datetime_values()
                )
                # self.time_last_publish = now

    def register_details_in_blocks(self, custom_read=None):

        # Extract the registers reg_name, scalar, offet and location as lists
        # from the config file
        if custom_read == None:
            reg_names = self.get_config_section_and_key_list("basic_read_registers", "reg_name")
            reg_scalars = self.get_config_section_and_key_list("basic_read_registers", "scalar")
            reg_offsets = self.get_config_section_and_key_list("basic_read_registers", "offset")
            config_register_addrs = self.get_config_section_and_key_list("basic_read_registers", "location")
            reg_dtypes = self.get_config_section_and_key_list("basic_read_registers", "dtype")
            registers_blocks = self.get_config()["basic_read_block"]
        else:
            reg_names = self.get_map_section_and_key_list(custom_read["registers"], "reg_name")
            reg_scalars = self.get_map_section_and_key_list(custom_read["registers"], "scalar")
            reg_offsets = self.get_map_section_and_key_list(custom_read["registers"], "offset")
            config_register_addrs = self.get_map_section_and_key_list(custom_read["registers"], "location")
            reg_dtypes = self.get_map_section_and_key_list(custom_read["registers"], "dtype")
            registers_blocks = custom_read["blocks"]

        polarity = self.get_polarity()
        reg_scalars = [scalar * polarity for scalar in reg_scalars]
        
        
        reg_names_blocked_final = []
        reg_scalars_blocked_final = []
        reg_offsets_blocked_final = []
        reg_dtypes_blocked_final = []
        
        
        # Create a list containing register addresses to be read in decimal
        total_block_registers_read = [] # total number of registers read, may include extra registers not required
        for block in registers_blocks:
            start = block["start"]
            size = block["size"]
            # total_registers_read.extend(list(range(start, start + size)))
            total_block_registers_read = list(range(start, start + size))

            total_block_registers_read.sort()

            # Create a list of register address blocks to scan. Mark the registers 
            # to skip as unused_###
            reg_names_blocked = []
            reg_scalars_blocked = []
            reg_offsets_blocked = []
            reg_dtypes_blocked = []
            reg_locations_blocked = []
            # count = 0
            # rounds = 0
            # print("START READING BLOCKS")
            # print(f"total registers read: {total_block_registers_read}")
            # print(f"reg locations: {config_register_addrs}")
            
            for reg_addr in total_block_registers_read:
                
                # If the register addr read is one in the config save its details
                if reg_addr in config_register_addrs:
                    # get index where location appears in config_register_addrs
                    index = config_register_addrs.index(reg_addr)
                    reg_names_blocked.append(reg_names[index])
                    reg_scalars_blocked.append(reg_scalars[index])
                    reg_offsets_blocked.append(reg_offsets[index])
                    reg_dtypes_blocked.append(reg_dtypes[index])
                    reg_locations_blocked.append(reg_dtypes[index])
                    # rounds += 1
                    
                # otherwise need to handle a read register we are not interested in.
                # if the register is part of a 32 bit register pair, we don't do anything
                # if the register is not part of any pair then we mark it as unused
                else:
                    index_total = total_block_registers_read.index(reg_addr)
                    
                    if index_total != 0:
                        # get register before the one we are inspecting
                        prev_reg = total_block_registers_read[index_total - 1]
                        
                        if prev_reg in config_register_addrs:
                            prev_reg_config_index = config_register_addrs.index(prev_reg)
                            prev_reg_type = reg_dtypes[prev_reg_config_index]
                        else:
                            reg_names_blocked.append("unused_" + str(reg_addr))
                            reg_scalars_blocked.append(1)
                            reg_offsets_blocked.append(0)
                            reg_dtypes_blocked.append("h")
                            continue
                        
                        # if the previous register was a double then ignore the current one
                        if self.check_double_register(prev_reg_type):
                            continue
                        
                        # if the previous register was a single mark current as unused
                        else:
                            reg_names_blocked.append("unused_" + str(reg_addr))
                            reg_scalars_blocked.append(1)
                            reg_offsets_blocked.append(0)
                            reg_dtypes_blocked.append("h")
                            continue
                            
            reg_names_blocked_final.extend(reg_names_blocked)
            reg_scalars_blocked_final.extend(reg_scalars_blocked)
            reg_offsets_blocked_final.extend(reg_offsets_blocked)
            reg_dtypes_blocked_final.extend(reg_dtypes_blocked)
                    
        # print(f"\n\nreg_names_blocked === {reg_names_blocked_final}")
        # print(f"\nreg_scalars_blocked === {reg_scalars_blocked_final}")
        # print(f"\nreg_offsets_blocked === {reg_offsets_blocked_final}")
        # print(f"\nreg_dtypes_blocked === {reg_dtypes_blocked_final}\n\n")
        
        return reg_names_blocked_final, reg_scalars_blocked_final, reg_offsets_blocked_final, reg_dtypes_blocked_final

    def update_read(self, custom_read=None):
        """
        Queries the device and reads the chosen registers. The current device
        state is returned.

        If custom_read == None then only the "basic_read_registers" from the 
        device config file will be read for the device. If you wish to read a 
        different set of registers, custom_read needs to be a map that has the
        following structure:
        {
            "reading_type": <type of reading performed e.g. basic/voltage/temperature >
            "registers": <list of registers to read>,
            "blocks": <list of register blocks to read>
        }
        """
        reg_names, reg_scalars, reg_offsets, reg_dtypes = self.register_details_in_blocks(custom_read=custom_read)
        # print(f"lengthe of reg names == {len(reg_names)}")
        unpack_string = "".join(reg_dtypes)
        # print(reg_dtypes)
        
        if custom_read == None:
            registers_to_read = self.get_config()["basic_read_block"]
            self.set_reading_type('basic')
        else:
            registers_to_read = custom_read["blocks"]
            self.set_reading_type(custom_read["reading_type"])
        registers_tuple = []
        for reg in registers_to_read:
            registers_tuple.append((reg["start"], reg["size"]))

        raw_regs = self.read_modbus(registers_tuple)
        
        
        # decoder = BinaryPayloadDecoder.fromRegisters(raw_regs, byteorder=Endian.Big, wordorder=Endian.Big)
        # print(f"decoded with binary payload builder: {raw_regs}")
        # # print(f"decoded with binary payload builder: {decoder.decode_32bit_float()}")
        # print(f"decoded with binary payload builder: {decoder.decode_16bit_uint()}")
        
        
        
        
        # print(f"raw reg results = {raw_regs}\n")
        # raw_bytes = np.array(raw_regs).tobytes()
        raw_bytes = np.array(raw_regs, dtype='<u2').tobytes()
        # print(f"raw bytes == {len(raw_bytes)}")

        # print(f"unpack string: {unpack_string}")
        # print(f"{len(unpack_string)}")
        # print(f"raw bytes: {raw_bytes}")
        # print(f"length of raw bytes: {len(raw_bytes)}")
        
        # print(reg_names)
        # reg_bytes_list = []
        # reg_locs = range(229, 246)
        # for index, byte in enumerate(raw_bytes):
        #     if index > 1 and index % 2 == 0:
        #         reg_bytes_list.append(f"{raw_bytes[index-2:index]}")
        #         # print(f"{raw_bytes[index-2:index]}")
                
        # print(f"{len(reg_locs)} {len(reg_bytes_list)}")
        # for index in range(len(reg_locs)):
        #     print(f"{reg_locs[index]} : {reg_bytes_list[index]}")
            
            
        # print(reg_bytes_list[0])
        # raw_229 = int.from_bytes(reg_bytes_list[0], byteorder='big')
        # raw_230 = int.from_bytes(reg_bytes_list[1], byteorder='big')
        
        # full_int = (raw_229 << 16) + raw_230 
        
        # print(f"RESULT:    {full_int}")
        
        # concat raw bytes down to match length of unpack_string
        # raw_bytes_new_length = 0
        # for 
        
        # print("#################")
        # print(f"unpack string: {len(unpack_string)}    raw_bytes = {len(raw_bytes)}")
        values = struct.unpack('<' + unpack_string, raw_bytes)
        values = np.array(values)
        scalars = np.array(reg_scalars)
        offsets = np.array(reg_offsets)
        result = np.round((scalars * values) + offsets, 1).tolist() # convert np array to list
        # print(f"result after decode of bytes: {result}")
        results_obj = dict(zip(reg_names, result))
        

        # print(f"\n\n{results_obj}\n\n")
        for key in list(results_obj.keys()):
            
            if isinstance(results_obj[key], int):
                results_obj[key] = int(results_obj[key])
            if re.search("unused*", key):
                # print("Deleting register: " + key) #TODO: ERROR
                del results_obj[key]
        
        return results_obj

    def update(self):
        timestamp = datetime.now(tz=timezone.utc)
        self.get_state().update(datetime=timestamp)
        self.get_state().update(self.update_read())
