#!/usr/bin/env python3
import time
import sys
import os
from edge_device import Edge_device
import toml
from redis_message_structures import RedisEncoderDecoder
import db_logger
import logging
from redis_message_structures import CommandMessage, RedisEncoderDecoder

# Use either real getmac library for raspios or temporary copied one for buildroot 
import getmac
from utils_custom import Utils
get_mac_address = Utils.get_mac_address

logger_setup = db_logger.DBLogger(os.path.basename(__file__), logging.INFO)
logger = logger_setup.get_logger()

class Statcom(Edge_device):
    def __init__(self, module_name, host, port, unit_id, mode, version):
        
        self.new_version = True if version == "new" else False
        
        CONFIG_FILE = f'{os.path.dirname(__file__)}/../config/config_statcom_registers_new.toml' if self.new_version else f'{os.path.dirname(__file__)}/../config/config_statcom_registers.toml'
        
        self.config = toml.load(CONFIG_FILE)
        super().__init__(module_name, host, port, unit_id, True)
        
        # self.state = dict(SUN=None, time=None)
        # self.state = dict(device_id=self.get_device_id(), datetime=None)
        self.read_only_mode = True if mode == "read_only" else False
        # self.set_sleep_time()

    def start_loop(self):

        while True:
            now = time.time()
            if now > self.time_last_heartbeat + self.get_heartbeat_period():
                self.send_heartbeat()
                self.set_time_last_heartbeat(now)

            self.listen()
            self.sleep()
            # print(self.state)


    # def get_datetime_values(self):
    #     return ["time"]

    def get_config(self):
        return self.config

    def handle_command(self, command_data: str):
        command_dict: CommandMessage = RedisEncoderDecoder.decode_command(command_data)
        command = command_dict.command_key_word
        settings = command_dict.settings
        
        print(f"\nCOMMAND RECIEVED: {self.get_module_name()}\n\tcommand: {command}\n\tsetting: {settings}\n")

        logger.debug(f"COMMAND RECIEVED: '{self.get_module_name()}' program receiving command '{command}'")
        #TODO: ERROR

        if command == "start":
            self.start()
        elif command == "stop":
            self.stop()
        elif command == "set_power":
            if len(settings) == 0:
                print("No power setting provided.") #TODO: ERROR
                logger.warning("COMMAND: No power setting provided.")
            else:
                self.set_power(float(settings[0]))
        elif command == "set_powers_3p":
            if len(settings) < 3:
                print("Didn't provide all phase power settings.") #TODO: ERROR
                logger.warning("COMMAND: Didn't provide all phase power settings.")
            else:
                self.set_power_multiple_phases(int(settings[0]), int(settings[1]), int(settings[2]))
        elif command == "voltage_mode":
            self.set_mode_voltage()
        elif command == "current_mode":
            self.set_mode_current()
        elif command == "enable":
            self.set_drm_enable()
        elif command == "disable":
            self.set_drm_disable()
        elif command == "zero_var_mode":
            self.set_ac_reactive_power_zero()
        elif command == "manual_var_mode":
            self.set_ac_reactive_power_manual_mode()
        elif command == "volt_var_mode":
            self.set_ac_reactive_power_volt_mode()
        elif command == "set_reactive_power":
            self.set_reactive_power(float(settings[0]))
        else:
            # print("Command not recognised.") #TODO: ERROR
            logger.warning("COMMAND: Command not recognised.")

        self.update()


    def write_modbus(self, register_blocks):
        function_codes = []

        for start_register, register_values in register_blocks:
            response = self.client.write_registers(start_register, register_values, unit=self.get_unit_id())

            function_codes.append(response.function_code)

        return function_codes

    def start(self):
        self.client.write_registers(1050, [1], unit=self.get_unit_id()) # verified new statcom registers

    def stop(self):
        self.client.write_registers(1050, [0], unit=self.get_unit_id()) # verified new statcom registers

    def set_power(self, power): 
        target = power
        if target < 0:
            target += 65536
        target = [int(target)]*3
        self.client.write_registers(1000, target, unit=self.get_unit_id()) # verified new statcom registers
    
    def set_power_multiple_phases(self, power_1, power_2, power_3):
        print(power_1, power_2, power_3)
        
        if power_1 < 0:
            power_1 += 65536
        
        if power_2 < 0:
            power_2 += 65536
        
        if power_3 < 0:
            power_3 += 65536

        if self.new_version:
            self.client.write_registers(1000, [power_1, power_2, power_3], unit=self.get_unit_id())
        else:
            self.client.write_registers(1000, [power_3, power_1, power_2], unit=self.get_unit_id())

    # def get_state(self):
    #     return statcom_state_lookup[self.state[2046]]

    def set_mode_voltage(self):
        self.client.write_registers(1055, [1], unit=self.get_unit_id()) # verified new statcom registers

    def set_mode_current(self):
        self.client.write_registers(1055, [0], unit=self.get_unit_id()) # verified new statcom registers

    def set_drm_enable(self,): # verified new statcom registers
        self.client.write_registers(1048, [1], unit=self.get_unit_id()) #TODO(ed): check the correct register 

    def set_drm_disable(self,): # verified new statcom registers
        self.client.write_registers(1048, [0], unit=self.get_unit_id()) #TODO(ed): check the correct register

    def set_ac_reactive_power_zero(self):
        self.client.write_registers(1054, [0], unit=self.get_unit_id())
        
    def set_ac_reactive_power_manual_mode(self):
        self.client.write_registers(1054, [1], unit=self.get_unit_id())
        
    def set_ac_reactive_power_volt_mode(self):
        self.client.write_registers(1054, [2], unit=self.get_unit_id())
        
    def set_reactive_power(self, power):
        target = power
        if target < 0:
            target += 65536
        target = [int(target)]*3
            
        self.client.write_registers(1004, target, unit=self.get_unit_id())
        self.client.write_registers(1005, target, unit=self.get_unit_id())
        self.client.write_registers(1006, target, unit=self.get_unit_id())

if __name__ == "__main__":
    
    # argv[0] is name of this python program
    # argv[1] is name of this module in the system architecture (specific for each device)

    module_name = sys.argv[1]
    host = sys.argv[2]
    port = int(sys.argv[3])
    unit_id = int(sys.argv[4])
    mode = sys.argv[5]
    version = sys.argv[6]

    print("Connected to statcom on host: " + str(host) + " device_id: " + str(get_mac_address(ip=host)))
    statcom = Statcom(module_name, host, port, unit_id, mode, version)
    statcom.start_loop()
