from time import sleep
from subprocess import call
from .automodule import AutoModule
from .siad import Siad


class AutoRestart(AutoModule):
    def __init__(self, configuration_dictionary: dict, siad: Siad):
        self.siad = siad
        self.stop_commands = configuration_dictionary.get("stop-commands", [])
        sleep_duration = configuration_dictionary.get("sleep", "0")
        self.start_commands = configuration_dictionary.get("start-commands", [])
        cooldown = configuration_dictionary.get("cooldown", "0")

        self.sleep = float(sleep_duration)
        self.cooldown = float(cooldown)

    @property
    def name(self) -> str:
        return "AutoRestart" 

    def print_settings(self):
        self.print("Module enabled")
        if not self.stop_commands:
            self.print("Warning! Stop commands disabled")
        else:
            for cmd in self.stop_commands:
                self.print("Stop: $ {}".format(cmd))
        self.print("Sleep after stopping for {}s".format(self.sleep))
        if not self.start_commands:
            self.print("Warning! Stop commands disabled")
        else:
            for cmd in self.start_commands:
                self.print("Start: $ {}".format(cmd))
        self.print("Cooldown after starting for {}s".format(self.cooldown))

    def run_shell_command(self, command):
        self.print("Running command: $ {}".format(command))
        exit_code = call(command, shell=True)
        self.print("Exit code: {}".format(exit_code))

    def _run(self):
        while True:
            # After an error for 300 seconds
            run_restart_after_minutes = 5
            error_hits_max = 60

            error_hits = 0
            while error_hits < error_hits_max:
                try:
                    self.siad.get_host()
                    if error_hits > 0:
                        self.print("Siad reached successfully. Reset failure counter.")
                    error_hits = 0
                except Exception as e:
                    self.print("Siad failure {}/{} ({})".format(error_hits + 1, error_hits_max, e))
                    error_hits += 1
                sleep(run_restart_after_minutes)

            self.print("Start offline restart routine")
            for stop_command in self.stop_commands:
                self.run_shell_command(stop_command)
    
            self.print("Sleep after stop commands for {}s".format(self.sleep))
            sleep(self.sleep)

            for start_command in self.start_commands:
                self.run_shell_command(start_command)

            self.print("Cooldown after starting for {}s".format(self.cooldown))
            sleep(self.cooldown)
