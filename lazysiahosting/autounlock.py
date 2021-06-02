from time import sleep
from .automodule import AutoModule
from .siad import Siad, Result

class AutoUnlock(AutoModule):
    def __init__(self, configuration_dictionary: dict, siad: Siad):
        self.password = configuration_dictionary.get("wallet-password", None)
        self.siad = siad

        if self.password is None:
            raise ValueError(
                "Unlock module misses configuration "
                "parameter 'wallet-password'."
            )

    @property
    def name(self) -> str:
        return "AutoUnlock"

    def print_settings(self):
        self.print("Module enabled")

    def unlock(self):
        if self.siad.unlock_wallet(self.password) == Result.FAILURE:
            self.print("Failed unlocking the wallet. Retrying...")
        else:
            self.print("Unlocked Wallet")

    def _run(self):
        while True:
            if not self.siad.wallet_unlocked:
                self.unlock()
            sleep(10)
