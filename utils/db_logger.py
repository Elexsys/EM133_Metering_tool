#!/usr/bin/env python3
"""
DBLogger used to create logger and set configuration values.

Any logging handlers or formaters required are created here and added to the
DBLogger class instance.

Some Useful Recources for Python Logging:
https://zetcode.com/python/logging/
https://www.logicmonitor.com/blog/python-logging-levels-explained
https://stackoverflow.com/questions/32657771/python-logger-formatting-is-not-formatting-the-string
https://docs.python.org/3/howto/logging-cookbook.html
https://stackoverflow.com/questions/2314307/python-logging-to-database
https://www.youtube.com/watch?v=jxmzY9soFXg

The different level of logging levels are:
    DEBUG: Detailed information, typically of interest only when diagnosing 
    problems. Events that occur many times a day. The messages for this logging 
    level are only recorded by DB or txt.log when the module is in debug mode.
    (Only in scenarios where we want to debug something)

    INFO: Confirmation that things are working as expected. e.g. events that 
    happen a couple of times a day. This will be the minimum message level 
    inserted into db and txt.log so we don't want to set some logging event that
    happens hundreds of times a day to INFO (DEBUG is more suited)
    
    WARNING: An indication that something unexpected happened, or indicative of 
    some problem in the near future (e.g. 'disk space low'). The software is 
    still working as expected. e.g. device disconnected and reconnecting
    
    ERROR: Due to a more serious problem, the software has not been able to 
    perform some function. e.g. device connection completely failed
    
    CRITICAL: A serious error, indicating that the program itself may be unable 
    to continue running. Failed modules unable to restart
"""

import logging
import os
import sys
import datetime

LOGS_DIRECTORY =  f"{os.path.dirname(__file__)}/../logs/"
MSG_FORMAT = "%(asctime)s | %(name)s | %(levelname)s | %(funcName)s | %(message)s | Line Num=%(lineno)d"

logging.Formatter.formatTime = (lambda self, record, datefmt=None: datetime.datetime.fromtimestamp(record.created, datetime.timezone.utc).astimezone().isoformat(sep="T",timespec="milliseconds"))

class DBLogger():
    """
    Set up for a Python logging instance with custom handlers and formatters to 
    be used in modules that require logging.
    """

    def __init__(self, name: str, logger_level=logging.INFO) -> None:
        """
        Initialises a DBLogger.
        """
        self._name = name
        # self._module_name = self._name.split("/")[-1][:-3]
        self._module_name = self._name
        self._log_name = self._module_name + ".txt"
        self._log_path = LOGS_DIRECTORY + self._log_name
        if not os.path.isfile(self._log_path):
            with open(self._log_path, "a") as a:
                print(f"Created log file at: {self._log_path}.")

        # Create Logger with getLogger
        self.logger = logging.getLogger(self._name)

        # self._formatter = logging.Formatter(fmt=MSG_FORMAT, datefmt=DATE_FORMAT)
        self._formatter = logging.Formatter(fmt=MSG_FORMAT)

        # Create custom postgres handler
        # self._postgres_handler = logging_db_handler.LogDBHandler()###############
        # self._postgres_handler.setFormatter(self._formatter)
        # self._postgres_handler.setLevel(logger_level)

        # Create FileHandler to write to txt file
        self._file_handler = logging.FileHandler(self._log_path)
        self._file_handler.setFormatter(self._formatter)
        self._file_handler.setLevel(logger_level)

        # Create handler to print to terminal
        self._stream_handler = logging.StreamHandler(sys.stdout)
        self._stream_handler.setFormatter(self._formatter)
        self._stream_handler.setLevel(logger_level)

        # Add handler to logger
        # self.logger.addHandler(self._postgres_handler)
        self.logger.addHandler(self._file_handler)
        # self.logger.addHandler(self._stream_handler)
        self.logger.setLevel(logger_level)

    def get_logger(self):
        return self.logger