# **A tool for reading from the EM133 and writing values to a STATCOM.**


## **Requirements**

### Python

Must use Python version 3.11 or less. Which can be obtained from the link below.

https://www.python.org/downloads/release/python-3116/

### Packages
Install the required Pyhton packages from the provided ```requirements.txt``` with your prefered package manager. 

For the ```pip``` package manager, use the below command. 

```
pip install -r requirements.txt
```


## **Usage**

### Arguments

```
usage: EM133_meter_tool.py [-h] [--meter-addr METER_ADDR] [--statcom-addr STATCOM_ADDR] [-p PORT] [-F FREQ] [-q]

options:
  -h, --help            show this help message and exit
  --meter-addr METER_ADDR
                        Address of the Grid Meter.
  --statcom-addr STATCOM_ADDR
                        Address of the Statcom.
  -p PORT, --port PORT  Port used to connect to Grid Meter and Statcom.
  -F FREQ, --Freq FREQ  Measurement update frequency [Hz].
  -q                    Whether to run in quiet mode with no GUI.
```


### Example

Run the tool with a meter at the address ```192.168.1.222```, a statcom at ```192.168.1.111```, on port ```502``` at a rate of ```10 Hz```. 

```
python EM113_Meter_tool --meter-addr 192.168.1.222 --statcom-addr 192.168.1.111 -p 502 -F 10
```

To run in quiet mode with no GUI, add the ```-q``` flag.

```
python EM113_Meter_tool --meter-addr 192.168.1.222 --statcom-addr 192.168.1.111 -p 502 -F 10 -q
```

