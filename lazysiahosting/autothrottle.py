from sys import exit
from time import sleep, time
from subprocess import call
from threading import Thread
from .automodule import AutoModule
from .speedtest import Speedtest


def average(array: list) -> float:
    if not len(array):
        return 0
    return sum(array) / len(array)


def get_bytes_rx(interface: str):
    path = '/sys/class/net/{}/statistics/rx_bytes'.format(interface)
    with open(path, 'r') as f:
        return int(f.read())


def get_bytes_tx(interface: str):
    path = '/sys/class/net/{}/statistics/tx_bytes'.format(interface)
    with open(path, 'r') as f:
        return int(f.read())


class NetworkWatcher:
    """Watch your network.
    
    While doing the speedtest, your server might up- and
    download data, which means the speedtest would have inprecise results.
    By measuring the entire host traffic while testing, a good estimate can be made."""
    def __init__(self, interface: str, interval: float = 0.75):
        self.history_down_bps = []
        self.history_up_bps = []
        self._stop = False
        self.interface = interface
        self.interval = interval
        self.thread = Thread(target=NetworkWatcher.work, args=(self,))
        self.thread.start()

    def work(self):
        last_timestamp = time()
        bytes_rx = get_bytes_rx(self.interface)
        bytes_tx = get_bytes_tx(self.interface)

        while not self._stop:
            sleep(self.interval)
            pre_check_time = time()
            new_bytes_rx = get_bytes_rx(self.interface)
            new_bytes_tx = get_bytes_tx(self.interface)
            timedelta = time() - last_timestamp
            rx_bps = (new_bytes_rx - bytes_rx) * 8 / timedelta
            tx_bps = (new_bytes_tx - bytes_tx) * 8 / timedelta
            self.history_down_bps.append(rx_bps)
            self.history_up_bps.append(tx_bps)

            last_timestamp = pre_check_time
            bytes_rx = new_bytes_rx
            bytes_tx = new_bytes_tx

    def stop(self):
        self._stop = True
        self.thread.join()

    def __del__(self):
        self._stop = True

    def get_peak_tx_bps(self) -> int:
        best_of = list(sorted(self.history_up_bps))[-3:]
        return average(best_of)

    def get_peak_rx_bps(self) -> int:
        best_of = list(sorted(self.history_down_bps))[-3:]
        return average(best_of)


def perform_speed_test(interface: str) -> (int, int):
    s = Speedtest()
    s.get_best_server()

    network_watcher = NetworkWatcher(interface)
    s.download()
    s.upload()
    network_watcher.stop()

    bps_up = network_watcher.get_peak_tx_bps()
    bps_down = network_watcher.get_peak_rx_bps()

    return (bps_up, bps_down)


class AutoThrottle(AutoModule):
    def __init__(self, configuration_dictionary: dict):
        self.interface = configuration_dictionary.get("interface")
        self.throttle_command = configuration_dictionary.get("throttle-command")
        self.unthrottle_command = configuration_dictionary.get("unthrottle-command")
        interval = configuration_dictionary.get("interval")
        upload_factor = configuration_dictionary.get("up")
        download_factor = configuration_dictionary.get("down")

        if not self.interface:
            self.print("Configuration key 'interface' is missing.")
            exit(1)
        if not self.throttle_command:
            self.print("Configuration key '-' is missing.")
            exit(1)
        if not self.unthrottle_command:
            self.print("Configuration key 'unthrottle-command' is missing.")
            exit(1)
        if not interval:
            self.print("Configuration key 'interval' is missing.")
            exit(1)
        if not upload_factor:
            self.print("Configuration key 'up' is missing.")
            exit(1)
        if not download_factor:
            self.print("Configuration key 'down' is missing.")
            exit(1)

        self.interval = float(interval)
        self.upload_factor = float(upload_factor)
        self.download_factor = float(download_factor)

    @property
    def name(self) -> str:
        return "AutoThrottle"

    def print_settings(self):
        self.print("Module enabled")
        self.print("Speedtest every {}s".format(self.interval))
        self.print(
            "Throttling up x{} and down x{}"
            .format(self.upload_factor, self.download_factor)
        )
        self.print("Interface to use: {}".format(self.interface))
        self.print("Throttle command: $ {}".format(self.throttle_command))
        self.print("Unthrottle command: $ {}".format(self.unthrottle_command))

    def perform_speedtest_and_trottle(self):
        unthrottle_command = self.unthrottle_command.format(
            interface=self.interface
        )
        unthrottle_exit = call(unthrottle_command, shell=True)
        self.print('Unthrottle exit code: {}'.format(unthrottle_exit))

        bps_up, bps_down = perform_speed_test(self.interface)
        self.print(
            "Measured up: {}Mbits, down: {}Mbits"
            .format(
                bps_up / 1000 / 1000,
                bps_down / 1000 / 1000,
            )
        )
        target_bps_up = round(bps_up * self.upload_factor)
        target_bps_down = round(bps_down * self.download_factor)

        throttle_command = self.throttle_command.format(
            mbits_up=round(target_bps_up / 1000 / 1000),
            mbits_down=round(target_bps_down / 1000 / 1000),
            mbytes_up=round(target_bps_up / 1000 / 1000 / 8),
            mbytes_down=round(target_bps_down / 1000 / 1000 / 8),
            kbits_up=round(target_bps_up / 1000),
            kbits_down=round(target_bps_down / 1000),
            kbytes_up=round(target_bps_up / 1000 / 8),
            kbytes_down=round(target_bps_down / 1000 / 8),
            interface=self.interface,
        )
        self.print("$ {}".format(throttle_command))
        throttle_exit = call(throttle_command, shell=True)
        self.print("Throttle exit code: {}".format(throttle_exit))

    def _run(self):
        while True:
            self.perform_speedtest_and_trottle()
            sleep(self.interval)
