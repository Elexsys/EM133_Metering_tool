#!/usr/bin/env python3
import numpy as np
import sys
import os
import logging
import toml
import time

import db_logger
from edge_device import Edge_device
from utils_custom import Utils

# Use either real getmac library for raspios or temporary copied one for buildroot 
import getmac

get_mac_address = Utils.get_mac_address

LOGGER_LEVEL = logging.INFO

logger_setup = db_logger.DBLogger(os.path.basename(__file__), LOGGER_LEVEL)
logger = logger_setup.get_logger()

# import matplotlib.pyplot as plt

reg_read_row = [(63152, 33),
                (63288, 120),
                (63408, 120),
                (63528, 120),
                (63648, 120),
                (63768, 32)]

reg_write_select_row = [(63120, [11,128,65535,0,0,0]),
                        (63120, [11,128,65535,1,0,0]),
                        (63120, [11,128,65535,2,0,0]),
                        (63120, [11,128,65535,4,0,0]),
                        (63120, [11,128,65535,5,0,0]),
                        (63120, [11,128,65535,6,0,0])]

reg_write_begin_end = (63120, [1,128,0,65535])

modbus_unit_id = 1

waveform_names = ['A Volts',
                  'B Volts',
                  'C Volts',
                  'A Amps',
                  'B Amps',
                  'C Amps']

waveform_scalars = [0.1,
                    0.1,
                    0.1,
                    0.01,
                    0.01,
                    0.01]


CONFIG_FILE = f'{os.path.dirname(__file__)}/../config/config_meter_satec_registers.toml'

class Meter(Edge_device):
    def __init__(
            self, 
            module_name: str, 
            host: str, 
            port: int, 
            unit_id: int):
        
        self.config = toml.load(CONFIG_FILE)
        # print(f"METER MODULE NAME == {module_name}")

        super().__init__(
                module_name=module_name, 
                host=host, 
                port=port, 
                unit_id=unit_id, 
                uses_modbus=True)
        
        self.polarity = self.config["pretested_meter_polarities"][self.module_type]

        # self.state.update(device_id=self.get_device_id())
        # print("METER", module_name, self.get_polarity()) #TODO: ERROR
        logger.debug(f"EDGE DEVICE: meter={module_name}, polarity={self.get_polarity()}")

    def start(self):
        while True:
            now = time.time()
            self.listen()
            if now > self.get_time_last_heartbeat() + self.get_heartbeat_period():
                self.send_heartbeat() #TODO: CONFIG
                logger.debug(f"HEATBEAT: {self.get_heartbeat_topic()}")
                self.set_time_last_heartbeat(now)
            self.sleep()

# TODO: could sample on the second, or could depend on config for frequency for each device

    def get_polarity(self):
        return self.polarity

    def get_device_id(self):
        mac_regs = [(46176, 4)]
        raw_regs = self.read_modbus(mac_regs)
        raw_bytes = np.array(raw_regs, dtype=np.uint16).tobytes()
        device_id = raw_bytes.hex()
        return device_id

# TODO: return the waveform based on a trigger
    # def get_waveform(self):
    #     raw_waveform_data = []

    #     self.write_modbus([reg_write_begin_end])

    #     for registers in reg_write_select_row:
    #         self.write_modbus([registers])

    #         row_data = self.read_modbus(reg_read_row)

    #         raw_waveform_data.append(row_data)

    #     self.write_modbus([reg_write_begin_end])

    #     waveform_data = self.decode_waveform(raw_waveform_data)

    #     return waveform_data


    def decode_waveform(self, raw_waveform_data):
        waveform_data = []

        for idx, row in enumerate(raw_waveform_data):
            channel_offset = row[27]
            if channel_offset >= 32768:
                channel_offset = channel_offset - 65536
            channel_multiplier = row[28] + 65536 * row[29]
            channel_divisor = row[30]

            raw_data = row[33:]
            raw_data = np.array(raw_data, dtype=np.int16)
            raw_data = raw_data.astype(np.float)

            data = (raw_data - channel_offset) * channel_multiplier / channel_divisor

            data = data * waveform_scalars[idx]

            waveform_data.append(data)

        return waveform_data

    def get_datetime_values(self):
        return ["time"]

    def get_config(self):
        return self.config

    def handle_command(self, command):
        print("meter_satec_child.handle_command(): Meters cannot receive commands currently. Ignoring command...") #TODO: ERROR
        # Introduce logging once handle_command is coded


if __name__ == "__main__":
    
    # argv[0] is name of this python program
    # argv[1] is name of this module in the system architecture (specific for each device)

    module_name = sys.argv[1]
    host = sys.argv[2]
    port = int(sys.argv[3])
    unit_id = int(sys.argv[4])

    print("Connected to meter satec on host: " + host + " device_id: " + get_mac_address(ip=host)) #TODO: ERROR
    meter_grid = Meter(module_name, host, port, unit_id)
    meter_grid.start()