import json
import os
import pathlib
import sys
from datetime import datetime, timezone, timedelta, UTC
from time import sleep

import requests
import logging
from escpos.printer import Usb

logger = logging.getLogger(__name__)

last_printed_path = pathlib.Path("last_printed.json")


def last_printed_file_exists():
    if not last_printed_path.exists():
        logger.warning("File doesn't exist!")
        return False
    return True


def read_lastprinted_file() -> dict:
    if not last_printed_file_exists():
        return {}
    logger.info(f"Opening file: {last_printed_path}")
    with last_printed_path.open("r") as _ff:
        return json.loads(_ff.read())


def save_lastprinted_file(_data: dict):
    logger.info(f"Saving last printed file: {last_printed_path}")
    with last_printed_path.open("w") as _ff:
        json.dump(_data, _ff)


class Api:

    class ErrorNoResults(Exception):
        """
        Raised when API returned no results for given query.
        """
        def __init__(self, response, *args):
            self.response = response
            super().__init__(*args)

    class ErrorDrawSystemIdIsNone(ErrorNoResults):
        """
        Raised when drawSystemId is `None` for give query.
        Happens when prizes are not yet calculated on the server side (probably).
        """

    @property
    def default_games(self):
        return ["Lotto", "MiniLotto"]

    @property
    def api_key(self):
        return os.environ["LOTTO_API"]

    @property
    def headers(self):
        return {
            "accept": "application/json",
            "secret": self.api_key,
            "User-Agent": "https://github.com/bukowa/totolottoprinter"
        }

    def query_next_drawn_date(self, game: str):
        _url = f"https://developers.lotto.pl/api/open/v1/lotteries/info?gameType={game}"
        return requests.get(url=_url, headers=self.headers).json()

    def last_result_for_game(self, game: str):
        _url = f"https://developers.lotto.pl/api/open/v1/lotteries/draw-results/last-results-per-game?gameType={game}"
        _res1 = requests.get(_url, headers=self.headers)
        _res1.raise_for_status()
        _json1 = _res1.json()

        if len(_json1) == 0:
            raise Api.ErrorNoResults(_res1)

        r1 = None
        for r1 in _json1:
            if r1['gameType'] == game:
                break

        if r1 is None:
            raise Api.ErrorNoResults(_res1)

        if r1['drawSystemId'] is None:
            raise Api.ErrorDrawSystemIdIsNone(_res1)

        _url2 = f"https://developers.lotto.pl/api/open/v1/lotteries/draw-prizes/{game}/{r1['drawSystemId']}"
        _res2 = requests.get(_url2, headers=self.headers)
        _res2.raise_for_status()
        _json2 = _res2.json()

        r2 = None
        for r2 in _json2:
            if r2['gameType'] == game:
                break

        if r2 is None:
            raise Api.ErrorNoResults(_res2)

        return {
            "prizes": r2['prizes'],
            "drawDate": r2['drawDate'],
            "gameType": r2["gameType"],
            "drawSystemId": r2["drawSystemId"],
            "results": r1['results'][0]['resultsJson'],
            "specialResults": r1['results'][0]['specialResults'],
        }


def prizes_to_text(_result):
    """
    Convert prizes based on the game.
    """
    _gt = _result['gameType']
    _pr = _result['prizes']
    if _gt == "Lotto":
        return (
            f"6: ilosc: {_pr['1']['prize']} nagroda: {_pr['1']['prizeValue']}\n"
            f"5: ilosc: {_pr['2']['prize']} nagroda: {_pr['2']['prizeValue']}\n"
            f"4: ilosc: {_pr['3']['prize']} nagroda: {_pr['3']['prizeValue']}\n"
            f"3: ilosc: {_pr['4']['prize']} nagroda: {_pr['4']['prizeValue']}\n"
        )
    if _gt == "MiniLotto":
        return (
            f"5: ilosc: {_pr['1']['prize']} nagroda: {_pr['1']['prizeValue']}\n"
            f"4: ilosc: {_pr['2']['prize']} nagroda: {_pr['2']['prizeValue']}\n"
            f"3: ilosc: {_pr['3']['prize']} nagroda: {_pr['3']['prizeValue']}\n"
        )
    if _gt == "LottoPlus":
        return (
            f"6: ilosc: {_pr['1']['prize']} nagroda: {_pr['1']['prizeValue']}\n"
            f"5: ilosc: {_pr['2']['prize']} nagroda: {_pr['2']['prizeValue']}\n"
            f"4: ilosc: {_pr['3']['prize']} nagroda: {_pr['3']['prizeValue']}\n"
            f"3: ilosc: {_pr['4']['prize']} nagroda: {_pr['4']['prizeValue']}\n"
        )
    if _gt == "EuroJackpot":
        return (
            f"5+2: ilosc: {_pr['1']['prize']} nagroda:  {_pr['1']['prizeValue']}\n"
            f"5+1: ilosc: {_pr['2']['prize']} nagroda:  {_pr['2']['prizeValue']}\n"
            f"5+0: ilosc: {_pr['3']['prize']} nagroda:  {_pr['3']['prizeValue']}\n"
            f"4+2: ilosc: {_pr['4']['prize']} nagroda:  {_pr['4']['prizeValue']}\n"
            f"4+1: ilosc: {_pr['5']['prize']} nagroda:  {_pr['5']['prizeValue']}\n"
            f"3+2: ilosc: {_pr['6']['prize']} nagroda:  {_pr['6']['prizeValue']}\n"
            f"4+0: ilosc: {_pr['7']['prize']} nagroda:  {_pr['7']['prizeValue']}\n"
            f"2+2: ilosc: {_pr['8']['prize']} nagroda:  {_pr['8']['prizeValue']}\n"
            f"3+1: ilosc: {_pr['9']['prize']} nagroda:  {_pr['9']['prizeValue']}\n"
            f"3+0: ilosc: {_pr['10']['prize']} nagroda: {_pr['10']['prizeValue']}\n"
            f"1+2: ilosc: {_pr['11']['prize']} nagroda: {_pr['11']['prizeValue']}\n"
            f"2+1: ilosc: {_pr['12']['prize']} nagroda: {_pr['12']['prizeValue']}\n"
        )
    raise Exception(f"Unknown game: {_gt}")


def text_for_result(_result: dict):

    first = (f"Gra: {_result['gameType']}\n"
             f"Data: {datetime.fromisoformat(_result['drawDate']).astimezone(timezone(timedelta(hours=2)))}\n"
             f"Liczby: {' '.join([str(x) for x in _result['results']])}\n"
             )

    if len(_result['specialResults']) > 0:
        first += (f"Liczby specjalne: {' '.join([str(x) for x in _result['specialResults']])}\n"
                  )

    last = (f"Wyniki:\n{prizes_to_text(_result)}"
            f"\n\n"
            )

    return first + last


def printer_print(_text: str, retry=10):
    _p = Usb(
        idVendor=0x0416,
        idProduct=0x5011,
        profile="NT-5890K",
    )
    logger.info("Trying to print...")
    _p.text(_text)
    logger.info("Print success... (probably)")
    _p.close()
    del _p


# Lotto, LottoPlus, EuroJackpot, MultiMulti, MiniLotto, Kaskada, Keno, EkstraPensja, EkstraPremia, Szybkie600, ZakladySpecjalne
default_games = ["Lotto", "LottoPlus", "MiniLotto", "EuroJackpot"]


def main(games=None):
    logger.info("Checking games arg")
    if games is None:
        if len(sys.argv) > 1:
            games = sys.argv[1:]
        else:
            games = default_games

    logger.info("Reading last printed file")
    data = read_lastprinted_file()
    for game in games:
        if game not in data.keys():
            data[game] = {
                "nextDrawDate": None,
                "lastPrintDate": None,
            }
    save_lastprinted_file(data)

    api = Api()

    while True:
        for game in games:
            logger.info(f"Checking for {game}")

            try:
                result = api.last_result_for_game(game)

                if result['drawDate'] == data[game]['lastPrintDate']:
                    logger.info(f"Already printed {game} for {result['drawDate']}")
                else:
                    logger.info(f"Printing for {result['drawDate']}")
                    printer_print(text_for_result(result))
                    data[game]['lastPrintDate'] = result['drawDate']
                    save_lastprinted_file(data)

            except Api.ErrorNoResults:
                logger.warning(f"No results for {game}")

            except Api.ErrorDrawSystemIdIsNone:
                logger.warning(f"DrawDawnId is None for {game}")

            except requests.RequestException as exc:
                logger.exception(exc)
                logger.warning(f"http exception for {game}")

            except Exception as exc:
                # inform about errors to me?
                logger.exception(exc)
                logger.error("something bad happened, exit...")
                exit(1)

        logger.info("Sleeping for 5 minutes...")
        sleep(60 * 5)

if __name__ == '__main__':
    logger.setLevel(logging.INFO)
    logger.info(f"Startujemy na {sys.platform}")
    main()
