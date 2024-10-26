import os

import requests

games = ("Lotto, LottoPlus, EuroJackpot, MultiMulti, MiniLotto, "
         "Kaskada, Keno, EkstraPensja, EkstraPremia, Szybkie600, "
         "ZakladySpecjalne").split(", ")

def get_url_res(_game):
    return f"https://developers.lotto.pl/api/open/v1/lotteries/draw-results/last-results-per-game?gameType={_game}"

def get_url_prize(_game, draw_id):
    return f"https://developers.lotto.pl/api/open/v1/lotteries/draw-prizes/{_game}/{draw_id}"

def headers():
    return {
        "accept": "application/json",
        "secret": os.environ["LOTTO_API"],
        "User-Agent": "https://github.com/bukowa/totolottoprinter"
    }

res_data = {}

for game in games:
    url = get_url_res(game)
    res_data[game] = requests.get(get_url_res(game), headers=headers()).json()
