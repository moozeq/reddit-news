#!/usr/bin/env python3
import argparse
import json

import requests
import datetime
import math
from pathlib import Path


NOW = datetime.datetime.now()


class Logger:
    LEVELS = [
        '\033[41m',  # white on red bg
        '\033[31m',  # red
        '\033[33m',  # yellow
        '\033[36m',  # cyan
        '\033[37m'  # white
    ]
    R = "\x1b[0m"

    @staticmethod
    def format(string: str, level: int):
        l = Logger.LEVELS[level]
        return f'{l}{string}{Logger.R}'

    @staticmethod
    def p(string: str, level: int):
        print(Logger.format(string, level))


class Entry:
    IMPORTANCE = [
        10000,
        5000,
        1000,
        100,
        0
    ]

    def __init__(self, e: dict):
        self.title = e['title']
        self.dt = datetime.datetime.fromtimestamp(e['created'])
        self.dt_delta = (NOW - self.dt).total_seconds() / 3600.0
        self.upvote_ratio = e['upvote_ratio']
        self.score = e['score']
        for i, imp in enumerate(Entry.IMPORTANCE):
            if self.score >= imp:
                self.IMPORTANCE = i
                break
        self.url = e['url']

    def __str__(self):
        h = math.floor(self.dt_delta)
        return f'[{self.upvote_ratio:.2f}][{h:>2}h] {Logger.format(self.title, self.IMPORTANCE)}'

    def __eq__(self, other):
        return self.title == other.title

    def __hash__(self):
        return hash(self.title)


class Subreddit:
    def __init__(self, r: str):
        self.r = r
        self.path = Path(f'{r}.json')
        self.urls = [
            f'https://www.reddit.com/r/{r}/hot.json',
            f'https://www.reddit.com/r/{r}/top.json'
        ]
        if self.should_get():
            self.entries = self.update()

        self.entries = sorted(
            [
                Entry(n['data'])
                for n in self.load()
            ],
            key=lambda e: e.score, reverse=True
        )

    def __str__(self):
        return '\n'.join(str(e) for e in self.entries)

    def should_get(self) -> bool:
        if self.path.exists():
            mod_date = datetime.datetime.fromtimestamp(self.path.stat().st_mtime)
            if (NOW - mod_date).total_seconds() / 3600.0 < 1.0:
                return False
        return True

    def update(self):
        raw_entries = []
        for url in self.urls:
            response = requests.get(url, headers={'User-agent': 'orzel-czarny'})
            res = response.json()
            if response.status_code != 200:
                raise Exception(json.dumps(res, indent=4))
            else:
                raw_entries += res['data']['children']

        raw_entries = {
            e['data']['title']: e
            for e in raw_entries
        }
        raw_entries = list(raw_entries.values())

        with open(self.path, 'w') as f:
            json.dump(raw_entries, f, indent=4)

    def load(self) -> dict:
        with open(self.path) as f:
            return json.load(f)


def get_and_print(subreddit: str):
    sr = Subreddit(subreddit)
    print(sr)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Reddit news in concise form')
    parser.add_argument('-s', '--subreddit', type=str, default='worldnews', help='Subreddit to show')

    args = parser.parse_args()
    get_and_print(args.subreddit)
