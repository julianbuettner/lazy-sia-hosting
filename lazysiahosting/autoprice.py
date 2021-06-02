from time import sleep
from .automodule import AutoModule
from .siastats import Siastats
from .siad import Siad


def get_percentage_delta(f1, f2):
    """500, 505 => 1% delta"""
    return abs(1 - f1 / f2) * 100


class AutoPrice(AutoModule):
    def __init__(
        self,
        configuration_dictionary: dict,
        siad: Siad,
    ):
        self.siad = siad
        minimum_price = configuration_dictionary.get("minimum-price")
        collateral_factor = configuration_dictionary.get("collateral-factor")
        usd = configuration_dictionary.get("usd")
        siastats_rank = configuration_dictionary.get("siastats-rank")
        hostdb_rank = configuration_dictionary.get("hostdb-rank")

        if not minimum_price:
            raise ValueError(
                "Price module misses configuration "
                "parameter 'minimum-price'."
            )

        if not collateral_factor:
            raise ValueError(
                "Price module misses configuration parameter "
                "'collateral-factor'. A good start is a factor of 2."
            )

        if not (usd or siastats_rank or hostdb_rank):
            raise ValueError(
                "Price module misses configuration "
                "parameter 'usd', 'siastats-rank' or 'hostdb-rank'."
            )

        self.minimum_price = float(minimum_price)
        self.collateral_factor = float(collateral_factor)

        self.usd = None
        self.siastats_rank = None
        self.hostdb_rank = None

        if usd:
            self.usd = float(usd)
            return

        if siastats_rank:
            self.siastats_rank = int(siastats_rank)
            return

        if hostdb_rank:
            self.hostdb_rank = int(hostdb_rank)
            return

    @property
    def name(self) -> str:
        return "AutoPrice"

    def print_settings(self):
        self.print("Module enabled")
        self.print("Collateral factor: {}".format(self.collateral_factor))
        self.print("Minimum price: {}SC".format(self.minimum_price))
        if self.usd:
            self.print(
                "Keep price at ${}".format(self.usd)
            )
        elif self.hostdb_rank:
            self.print(
                "Set price to target hostdb rank #{}".format(self.hostdb_rank)
            )
        else:
            self.print(
                "Set price to target siastats rank #{}".format(self.siastats_rank)
            )

    def set_by_usd(self):
        raise NotImplementedError()

    def set_price_by_rank_delta(self, delta):
        """+3 means, we have to rank better.
        -3 means we have to rank worse.
        
        Example: Current rank #42, target rank #45.
        So the delta is -3. We have to rank worse,
        meaning increase the price.
        """
        self.print("Rank delta: {}".format(delta))
        current_price = self.siad.storage_price
        new_price = current_price * 0.99 ** delta
        new_price = max(self.minimum_price, new_price)
        self.print("New price: {}".format(new_price))

        self.siad.storage_price = new_price
        self.siad.collateral = new_price * self.collateral_factor

    def set_by_hostdb(self):
        rank_price = self.siad.get_hostdb_rank_and_price()
        if rank_price is None:
            self.print("Error: Could not get host rank. Hostdb not up to date?")
            return
        
        rank, price = rank_price
        current_price = self.siad.storage_price

        self.print("Hostdb current rank #{}".format(rank))
        if get_percentage_delta(price, current_price) > 0.1:
            # More than 0.1% deviation
            # HostDB not up to date => wait
            self.print("Hostdb not up to date. Retry later.")
            return

        rank_delta = self.hostdb_rank - rank
        self.set_price_by_rank_delta(rank_delta)

    def set_by_siastats(self):
        siastats = Siastats(self.siad)
        siastats_actual_rank = siastats.rank

        self.print("Siastats current rank #{}".format(siastats_actual_rank))

        price = siastats.storage_price
        current_price = self.siad.storage_price
        if get_percentage_delta(price, current_price) > 0.1:
            # More than 0.1% deviation
            # Siastats not up to date => wait
            self.print("Siastats not up to date. Retry later.")
            return

        rank_delta = self.siastats_rank - siastats_actual_rank
        self.set_price_by_rank_delta(rank_delta)

    def _run(self):
        while True:
            if self.usd:
                self.set_by_usd()
            elif self.hostdb_rank:
                self.set_by_hostdb()
            else:
                self.set_by_siastats()
            sleep(300)  # 5min
