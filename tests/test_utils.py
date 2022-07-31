from src.utils import DotDotSlash
from pathlib import Path
import sqlite3

def test_urls():
    TARGET = "file.txt"
    URL_TEMPLATE = "https://www.example.com/image?filename=%s"
    URL = URL_TEMPLATE % TARGET
    DEPTH = 1

    dds = DotDotSlash(
        url    = URL,
        target = TARGET
    )

    cur = dds._connection.cursor()

    urls = cur.execute("SELECT url, word, depth FROM urls").fetchall()

    for url, word, depth in urls:
        assert url.startswith(URL_TEMPLATE % '')
        assert not url.startswith(URL)
        assert url.endswith(word)
        assert depth <= DEPTH
    
    dds.call_endpoint("http://www.google.com", "c:\\boot.ini")
    