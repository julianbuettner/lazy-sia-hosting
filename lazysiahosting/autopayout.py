from time import sleep, time
from .automodule import AutoModule
from .siad import Siad


class TransactionJob:
    def __init__(
        self,
        name: str,
        address: str,
        amount: float,
    ):
        self.name = name
        self.address = address
        self.amount = amount

    def __str__(self) -> str:
        return "[{} {}SC => {}]".format(
            self.name, self.amount, self.address
        )

def block_to_transaction_jobs(block: list) -> list:
    transaction_jobs = []

    if not isinstance(block, list):
        print("Invalid payout block. Check your configuration.")

    for element in block:
        name = element.get("name")
        address = element.get("address")
        amount = element.get("amount")

        if not name:
            print("Payoutblock element misses key 'name'")
            exit(1)
        if not address:
            print("Payoutblock element misses key 'address'")
            exit(1)
        if not amount:
            print("Payoutblock element misses key 'amount'")
            exit(1)

        transaction_jobs.append(TransactionJob(name, address, float(amount)))
    return transaction_jobs


def blocksize_from_block(block) -> float:
    block_sum = 0
    for entry in block:
        block_sum += max(entry.amount, 0)
    return block_sum


class AutoPayout(AutoModule):
    def __init__(self, configuration_dictionary: dict, siad: Siad):
        self.siad = siad
        minimum_available = configuration_dictionary.get("minimum-available")
        sleep_after = configuration_dictionary.get("sleep-after")

        block = configuration_dictionary.get("block")

        if not minimum_available:
            self.print("Missing config key 'minimum-available'")
            exit(1)
        if not sleep_after:
            self.print("Missing config key 'minimum-available'")
            exit(1)
    
        self.minimum_available = float(minimum_available)
        self.sleep_after = float(sleep_after)
        self.block = block_to_transaction_jobs(block)

    @property
    def name(self) -> str:
        return "AutoPayout"

    def print_settings(self):
        self.print("Module activated")
        self.print("Always keeping {}SC in the wallet".format(self.minimum_available))
        self.print("The payout block has the following payouts:")
        for entry in self.block:
            self.print(entry)
        self.print("After payout sleep for {}s".format(self.sleep_after))

    def perform_payout(self):
        blocksize = blocksize_from_block(self.block)
        balance = self.siad.balance
        payout_threshold = self.minimum_available + blocksize

        if payout_threshold > balance:
            self.print("No payout: {}SC < {}SC".format(balance, payout_threshold))
            return

        self.print("Performing payout")
        for entry in self.block:
            result = self.siad.send_siacoins(
                amount_in_siacoins_not_hastings=entry.amount,
                address=entry.address,
            )
            self.print("Payout result {} {}".format(entry, result))

        self.print("Payout done")

    def _run(self):
        while True:
            self.perform_payout()
            sleep(self.sleep_after)