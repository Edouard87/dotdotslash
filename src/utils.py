from src.match import befvar, dotvar, match
from os.path import exists
from os import remove, getcwd
import sys
from pathlib import Path
import requests
import asyncio
import aiohttp

DEFAULT_URL_PATH = (Path(getcwd()) / "urls.txt").absolute()

def create_links(
    url: str,
    target: str,
    depth: int = 0,
    force = False,
    file: str = DEFAULT_URL_PATH,
    include: list = ["windows","linux","apache","php"]):
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
    
    URL_FILE = Path(file)

    if exists(URL_FILE.absolute()):
        if not force:
            raise Exception("URL File already exists.")
        else:
            remove(URL_FILE.absolute())

    WORDS = []
    include = [s.lower() for s in include]

    for possible_system, system_words in match.items():
        # match.keys returns the systems. Each system is itself a dict.
        if possible_system in include:
            WORDS.extend(list(system_words.keys()))

    with open(URL_FILE.absolute(),"a") as f:
        duplicate = []
        f.write(str(depth) + '\n') # first line of file is depth.
        for count in range(depth + 1):
            for var in dotvar:
                for bvar in befvar:
                    for word in WORDS:
                        rewrite = bvar + (var * count) + word
                        fullrewrite = url.replace(target, rewrite)
                        if fullrewrite not in duplicate:
                            # save to the file
                            f.write(fullrewrite + '\n')
                            duplicate.append(fullrewrite)

async def call_endpoint(endpoint: str):
    '''
    Sends a request to the provided endpoint and runs checks on the data.
    '''
    async with aiohttp.ClientSession() as s:
        pass


def dispatch(file: str = DEFAULT_URL_PATH):
    '''
    Dipatches the requests in the provided file. Makes use of coroutines to speed up the task.
    :param: file - The file containing the URLs to disptach.
    '''
    tasks = set()
    with open(file) as f:
        f.read() # first line is depth. Not relevant here.
        while (line := f.readline()):
            tasks.add(asyncio.create_task(call_endpoint(line)))

