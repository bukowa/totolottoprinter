import os

import requests
import ifaddr
from escpos.printer import Usb


def print_ipaddress(_printer: Usb):
    adapters = ifaddr.get_adapters()

    for adapter in adapters:
        if adapter.nice_name == 'wlan0':
            for ip in adapter.ips:
                if ip.is_IPv4:
                    print(ip.ip)
                    p.text(f"{ip.ip}\n")

lotto_api = os.environ["LOTTO_API"]
headers = {
    "accept": "application/json",
    "secret": lotto_api,
    "User-Agent": "Mateusz Kurowski - aplikacja dla mojego dziadka"
}
url = "https://developers.lotto.pl/api/open/v1/lotteries/draw-results/last-results"

data = requests.get(url, headers=headers)
jdata = data.json()
data.raise_for_status()

p = Usb(
    idVendor=0x0416,
    idProduct=0x5011,
    profile="NT-5890K",
)
print_ipaddress(p)
print("Done")