from requests import (
    get,
    post,
)
from requests.auth import HTTPBasicAuth
from enum import Enum

TERRABYTE_BYTES = 1e12
BLOCKS_PER_MONTH = 4320

class Result(Enum):
    SUCCESS = False
    FAILURE = True


def hastings_to_siacoin(h: str) -> float:
    return int(h) / 1e24

def siacoin_to_hastings(sc: float) -> str:
    return str(int(sc * 1e24))


def tiny_price_to_big_price(hastings: str) -> float:
    """Hastings per byte per block to SC per TB per month."""
    return hastings_to_siacoin(
        int(hastings) * TERRABYTE_BYTES * BLOCKS_PER_MONTH
    )

def big_price_to_tiny_price(siacoins: float) -> int:
    """SC per TB per month to hastings per byte per block."""
    return round(
        int(siacoin_to_hastings(siacoins))
        / TERRABYTE_BYTES / BLOCKS_PER_MONTH
    ) 


class Siad:
    """Communicate with the service siad."""

    def __init__(
        self,
        host: str,
        api_password: str,
    ):
        self.host = host
        self.api_password = api_password

    @property
    def public_hostname(self) -> str:
        return self.get_host()['externalsettings']['netaddress']

    @property
    def storage_price(self) -> float:
        price_hastings = int(self.get_host()['internalsettings']['minstorageprice'])
        return tiny_price_to_big_price(price_hastings)

    @storage_price.setter
    def storage_price(self, price_in_siacoins: float):
        hastings_byte_block = big_price_to_tiny_price(price_in_siacoins)
        self.set_host('minstorageprice', hastings_byte_block)

    @property
    def hastings_per_siacoin(self) -> int:
        return int(self.get_consensus()['siacoinprecision'])

    @property
    def collateral(self) -> float:
        price_hastings = int(self.get_host()['internalsettings']['collateral'])
        return tiny_price_to_big_price(price_hastings)

    @collateral.setter
    def collateral(self, price_in_siacoins: float):
        hastings_byte_block = big_price_to_tiny_price(price_in_siacoins)
        self.set_host('collateral', hastings_byte_block)

    @property
    def wallet_unlocked(self) -> bool:
        return self.get_wallet()['unlocked']

    @property
    def pubkey(self) -> str:
        host = self.get_host()
        pubkey = "{}:{}".format(
            host["publickey"]["algorithm"],
            host["publickey"]["key"],
        )

    @property
    def balance(self) -> float:
        wallet = self.get_wallet()
        return hastings_to_siacoin(wallet["confirmedsiacoinbalance"])

    def request(self, method, uri, headers: dict = {}, **kwargs):
        headers['User-Agent'] = 'Sia-Agent'
        auth = HTTPBasicAuth('', self.api_password)
        url = 'http://' + self.host + uri
        return method(url, headers=headers, auth=auth, **kwargs)

    def set_host(self, key, value):
        return self.request(
            post, '/host?{}={}'.format(key, value)
        )

    def get_host(self) -> dict:
        res = self.request(
            get, '/host'
        )
        return res.json()

    def get_wallet(self) -> dict:
        res = self.request(
            get, '/wallet'
        )
        return res.json()

    def get_consensus(self) -> dict:
        res = self.request(
            get, '/consensus'
        )
        return res.json()

    def unlock_wallet(self, walletpassword: str) -> Result:
        res = self.request(
            post, '/wallet/unlock',
            params={'encryptionpassword': walletpassword},
        )
        if not res.text:
            return Result.SUCCESS
        if "wallet has already been unlocked" in res.text:
            return Result.SUCCESS
        return Result.FAILURE

    def get_hostdb_rank_and_price(self):
        res = self.request(
            get, '/hostdb/active'
        ).json()

        self_public_address = self.public_hostname
        for i in range(len(res["hosts"])):
            if res["hosts"][i]["netaddress"] == self_public_address:
                # Reversed, #1 is best (#0 does not exist)
                index = len(res["hosts"]) - i
                price = tiny_price_to_big_price(res["hosts"][i]["storageprice"])
                return (index, price)

        return None

    def send_siacoins(self, amount_in_siacoins_not_hastings: float, address: str):
        res = self.request(
            post, "/wallet/siacoins",
            data={
                "amount": siacoin_to_hastings(amount_in_siacoins_not_hastings),
                "destination": address,
            }
        )
        return res.json()


