#!/usr/bin/env python3

import sys
import os
sys.path.append(f"{os.path.dirname(__file__)}/utils")

from utils.statcom_child import Statcom
from utils.meter_satec_child import Meter

import argparse
import curses
import time


class Monitor:
    statcom_addr: str
    meter_addr: str
    port: int
    gui: bool
    meter_grid: Meter
    statcom: Statcom
    reg_meter_grid: dict
    reg_statcom: dict
    update_freq: float
    update_time: float

    def __init__(
        self,
        meter_addr: str,
        statcom_addr: str,
        port: int,
        update_freq: float,
        gui: bool = True,
    ) -> None:
        # CLI Setup
        self.gui = gui

        if self.gui:
            self.screen = curses.initscr()

            curses.start_color()
            curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)
            curses.init_pair(2, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
            curses.init_pair(3, curses.COLOR_GREEN, curses.COLOR_BLACK)
            curses.init_pair(4, curses.COLOR_BLACK, curses.COLOR_WHITE)

            self._max_unit_width = 5

            self._title_row = 1

            self._freq_row = self._title_row + 2

            self._meter_title_row = self._freq_row + 2
            self._meter_name_row = self._meter_title_row + 2
            self._meter_name_col = 5
            self._max_mater_name_width = 11
            self._meter_value_col = (
                self._meter_name_col + self._max_mater_name_width + 4
            )
            self._max_meter_value_width = 6
            self.meter_unit_col = (
                self._meter_value_col + self._max_meter_value_width + 1
            )

            self._statcom_title_row = self._meter_title_row
            self._statcom_name_row = self._statcom_title_row + 2
            self._statcom_name_col = self.meter_unit_col + self._max_unit_width + 5
            self._max_statcom_name_width = 28
            self._statcom_value_col = (
                self._statcom_name_col + self._max_statcom_name_width + 4
            )
            self._max_statcom_value_width = 5
            self._statcom_unit_col = (
                self._statcom_value_col + self._max_statcom_value_width + 1
            )

            self._screen_min_h = self._statcom_unit_col + self._max_unit_width
            self._screen_min_w = self._meter_name_row + 14

        # Statcom and Meter params
        self.statcom_addr = statcom_addr
        self.meter_addr = meter_addr
        self.port = port

        self.meter_grid = Meter(
            module_name="meter_grid_1", host=self.meter_addr, port=self.port, unit_id=12
        )
        self.statcom = Statcom(
            module_name="statcom_1",
            host=self.statcom_addr,
            port=self.port,
            unit_id=12,
            version="new",
            mode="read/write",
        )

        self.reg_meter_grid = self.meter_grid.update_read()
        self.reg_statcom = self.statcom.update_read()

        self._screen_refresh_time = 0.2
        self._screen_old_time = time.perf_counter()

        self.update_freq = update_freq
        self.update_time = 1 / self.update_freq
        self._update_old_time = time.perf_counter()

    def _check_screen(self):
        passed = True
        self.screen.refresh()
        width, height = self.screen.getmaxyx()
        if height < self._screen_min_h or width < self._screen_min_w:
            if self.gui:
                print(
                    "\n\n\rScreen size is too small for GUI... Falling back to quiet mode.\n\r\n"
                )
            self.gui = False
            passed = False
        elif not self.gui and (
            height >= self._screen_min_h and width >= self._screen_min_w
        ):
            self.screen = curses.initscr()
            self.gui = True

        return passed

    def _print_headings(self):
        self.screen.addstr(
            1, self._meter_name_col, "Meter to Statcom Controller", curses.color_pair(4)
        )

        self.screen.addstr(
            self._meter_title_row,
            self._meter_name_col,
            "Grid Meter",
            curses.color_pair(4),
        )
        self.screen.addstr(
            self._statcom_title_row,
            self._statcom_name_col,
            "Statcom",
            curses.color_pair(4),
        )

        self.screen.addstr(
            self._freq_row, self._meter_name_col, "Update Freq:", curses.color_pair(1)
        )
        self.screen.addstr(
            self._freq_row,
            self._meter_name_col + 12 + 4,
            f"{self.update_freq}",
            curses.color_pair(3),
        )
        self.screen.addstr(
            self._freq_row,
            self._meter_name_col + 12 + 4 + 6,
            f"[Hz]",
            curses.color_pair(2),
        )

    def _print_meter_grid(self):
        row = self._meter_name_row
        for p_type in [["Apparent", "kVA"], ["Active", "kW"]]:
            for ph in range(3):
                self.screen.addstr(
                    row,
                    self._meter_name_col,
                    f"{p_type[0]} {ph+1}:",
                    curses.color_pair(1),
                )
                self.screen.addstr(
                    row,
                    self._meter_value_col,
                    f"{int(self.reg_meter_grid.get(f'{p_type[1]}_{ph+1}')):d}",
                    curses.color_pair(3),
                )
                self.screen.addstr(
                    row, self.meter_unit_col, f"[{p_type[1]}]", curses.color_pair(2)
                )
                row += 1

    def _print_statcom(self):
        row = self._statcom_name_row
        for direction in ["Export", "Generation"]:
            for p_type in [["Apparent", "kVA"], ["Active", "kW"]]:
                for ph in ["A", "B", "C"]:
                    self.screen.addstr(
                        row,
                        self._statcom_name_col,
                        f"{direction} {p_type[0]} {ph}:",
                        curses.color_pair(1),
                    )
                    self.screen.addstr(
                        row,
                        self._statcom_value_col,
                        f"{int(self.reg_statcom.get(f'{direction}_Meter_{p_type[0]}_Power_{ph}')):d}",
                        curses.color_pair(3),
                    )
                    self.screen.addstr(
                        row,
                        self._statcom_unit_col,
                        f"[{p_type[1]}]",
                        curses.color_pair(2),
                    )
                    row += 1
            self.screen.addstr(
                row,
                self._statcom_name_col,
                f"Statcom {direction} Lifesign:",
                curses.color_pair(1),
            )
            self.screen.addstr(
                row,
                self._statcom_value_col,
                f"{int(self.reg_statcom.get(f'{direction}_Meter_Lifesign')):d}",
                curses.color_pair(3),
            )
            row += 1

    def _timed_out(self, old_time: float, dt: float):
        if time.perf_counter() - old_time > dt:
            return True

    def _screen_timed_out(self):
        if self._timed_out(self._screen_old_time, self._screen_refresh_time):
            self._screen_old_time = time.perf_counter()
            return True

    def _update_timed_out(self):
        if self._timed_out(self._update_old_time, self.update_time):
            self._update_old_time = time.perf_counter()
            return True

    def _get_meter_grid_power(self):
        kVA_meter = []
        kW_meter = []
        for ph in range(3):
            val = self.reg_meter_grid.get(f"kVA_{ph+1}", None)
            if val is None:
                raise ValueError("Satec register missing kVA value.")
            val = int(val)
            if val < 0:
                val += 2**16
            kVA_meter += [val]

            val = self.reg_meter_grid.get(f"kW_{ph+1}", None)
            if val is None:
                raise ValueError("Satec register missing kW value.")
            val = int(val)
            if val < 0:
                val += 2**16
            kW_meter += [val]
        return kVA_meter, kW_meter

    def run_no_gui(self):
        print("Running without GUI...")
        while True:
            self._update()

    def _update(self):
        if self._update_timed_out():
            self.reg_meter_grid = self.meter_grid.update_read()
            self.reg_statcom = self.statcom.update_read()

            # Get values to be written to Statcom.
            kVA_meter, kW_meter = self._get_meter_grid_power()
            export_lifesign = int(self.reg_statcom.get("Export_Meter_Lifesign")) + 1
            generation_lifesign = (
                int(self.reg_statcom.get("Generation_Meter_Lifesign")) + 1
            )

            write_meter_regs = [
                [
                    1109,
                    kVA_meter
                    + kW_meter
                    + [export_lifesign]
                    + kVA_meter
                    + kW_meter
                    + [generation_lifesign],
                ]
            ]

            self.statcom.write_modbus(write_meter_regs)

    def _display(self, _):
        while True:
            self._update()

            if self._screen_timed_out() and self._check_screen():
                self.screen.clear()
                self._print_headings()
                self._print_meter_grid()
                self._print_statcom()
                self.screen.refresh()

    def run(self):
        if self.gui:
            curses.wrapper(self._display)
        else:
            self.run_no_gui()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--meter-addr",
        required=False,
        type=str,
        default="192.168.0.51",
        help="Address of the Grid Meter.",
    )
    parser.add_argument(
        "--statcom-addr",
        required=False,
        type=str,
        default="192.168.1.201",
        help="Address of the Statcom.",
    )
    parser.add_argument(
        "-p",
        "--port",
        required=False,
        type=int,
        default=502,
        help="Port used to connect to Grid Meter and Statcom.",
    )
    parser.add_argument(
        "-F",
        "--Freq",
        required=False,
        type=float,
        default=1.0,
        help="Measurement update frequency [Hz].",
    )
    parser.add_argument(
        "-q",
        required=False,
        action="store_true",
        help="Whether to run in quiet mode with no GUI.",
    )

    args = parser.parse_args()

    monitor = Monitor(
        meter_addr=args.meter_addr,
        statcom_addr=args.statcom_addr,
        port=args.port,
        update_freq=args.Freq,
        gui=not args.q,
    )
    monitor.run()
