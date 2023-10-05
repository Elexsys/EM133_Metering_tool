#!/usr/bin/env python3
from datetime import datetime, timezone
import os
import re
from getmac import get_mac_address

class Utils:

    @staticmethod
    def datetime_to_epoch(datetime: datetime) -> float:
        return datetime.timestamp()
    
    @staticmethod
    def get_module_name(module_path: str, nested_module_name=False) -> str:
        if nested_module_name == False:
            return os.path.basename(module_path).rsplit(".", 1)[0]
        else:
            # module_name = os.path.basename(module_path).rsplit(".", 1)[0]
            # module_folder = 
            # return os.path.basename(module_path).rsplit(".", 2)[0]
            return
    
    @staticmethod
    def get_mac_address(ip):
        """
        Functionality taken from python package getmac
        https://pypi.org/project/getmac/
        """
        # ping server to populate arp table
        os.system(f"ping -c 1 {ip} > /dev/null 2>&1")
        
        # read /proc/net/arp and pattern match to find the mac for
        # the given ip
        MAC_RE_COLON = r"([0-9a-fA-F]{2}(?::[0-9a-fA-F]{2}){5})"
        filepath = os.environ.get("ARP_PATH", "/proc/net/arp")
        with open(filepath) as f:
            data = f.read()
            match = re.search(re.escape(ip) + r" .+" + MAC_RE_COLON, data)
            return match.group(1)
        
    @staticmethod
    def write_to_tmp_file(content):
        f = open("tmp.txt", "w") # write
        # f = open(file_name, "a") # append
        f.write(content)
        f.close()

    
def main():
    MAC_RE_COLON = r"([0-9a-fA-F]{2}(?::[0-9a-fA-F]{2}){5})"

    
    # print(get_mac_address(interface="eth0", ip="192.168.0.1", network_request=True))
    filepath = os.environ.get("ARP_PATH", "/proc/net/arp")  
    with open(filepath) as f:
        data = f.read()
        print(data)

        match = re.search(re.escape("192.168.0.101") + r" .+" + MAC_RE_COLON, data)
        print(match.group(1))
        
    
if __name__ == "__main__":
    print(Utils.get_mac_address('192.168.0.101'))
