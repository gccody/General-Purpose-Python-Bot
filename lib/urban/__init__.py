import random

import requests
from bs4 import BeautifulSoup


class UrbanDictionary:
    BASE = "https://urbandictionary.com"

    def define_word(self, word: str) -> list[str]:
        if not word:
            raise ValueError('Must pass a word.')

        url = f'{self.BASE}/define.php'

        req = requests.get(url, params={'term': word})

        soup = BeautifulSoup(req.text, features="html.parser")

        meaning_tags = soup.find_all('div', {'class': 'meaning'})

        definitions: list[str] = [t.text for t in meaning_tags]

        return definitions
