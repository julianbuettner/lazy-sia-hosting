"""Template for modules"""
import traceback
from time import sleep

EXCEPTION_RESTART_COOLDOWN = 120


class AutoModule:
    """Inherit to implement a module."""
    def __init__(self, configuration_dictionary: dict):
        """Validate configuration, raise ValueError if invalid."""
        raise NotImplementedError()

    @property
    def name(self) -> str:
        raise NotImplementedError()

    def print(self, *args, **kwargs):
        print("[{}]".format(self.name), *args, **kwargs)

    def print_settings(self):
        raise NotImplementedError()

    def _run(self):
        raise NotImplementedError()

    def run(self):
        """Do the magic, restart in case of a thrown exception."""
        while True:
            self.print("Start module")
            try:
                self._run()
            except Exception:
                print(
                    "# ========\n"
                    "# Uncaught exception in module: {}\n"
                    "# ========"
                    .format(self.name)
                )
                traceback.print_exc()
                print(
                    "# ========\n"
                    "# Restarting module in two minutes.\n"
                    "# ========"
                )
                sleep(EXCEPTION_RESTART_COOLDOWN)


