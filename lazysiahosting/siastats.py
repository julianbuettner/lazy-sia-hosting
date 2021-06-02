from requests import (
    get,
    post,
)
from .siad import Siad


class Siastats:
    def __init__(self, siad: Siad):
        self.siad = siad
        self.host_id = self.get_host_id(self.siad.public_hostname)

    @property
    def host(self) -> dict:
        return self.get_host(self.host_id)

    @property
    def rank(self) -> int:
        return self.host['rank']

    @property
    def online(self) -> bool:
        return self.host['online']

    @property
    def storage_price(self) -> float:
        return self.host['storagePrice']

    @property
    def storage_price_uptodate(self) -> bool:
        return abs(self.storage_price - self.siad.storage_price) < 0.1

    def request(self, method, uri, headers: dict = {}, **kwargs):
        url = 'https://siastats.info:3510' + uri
        return method(url, headers=headers, **kwargs)

    def get_all_hosts(self) -> dict:
        return self.request(
            post, '/hosts-api/allhosts',
            data={'network': 'sia', 'list': 'active'}
        ).json()

    def get_host_id(self, host_name: str) -> int:
        host_list = self.get_all_hosts()
        for host in host_list:
            if host['CurrentIp'] == host_name:
                return host['Id']
        return None

    def get_host(self, host_id: int):
        return self.request(
            get, '/hosts-api/host/{}'.format(host_id)
        ).json()
