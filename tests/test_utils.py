from src.utils import create_links
from pathlib import Path

def test_urls():
    TARGET = "file.txt"
    URL_TEMPLATE = "https://www.example.com/image?filename=%s"
    URL = URL_TEMPLATE % TARGET
    URL_FILE = "urls.txt"
    DEPTH = 1
    create_links(URL, TARGET, file=URL_FILE, force = True, depth=DEPTH)
    with open(URL_FILE) as f:
        assert str(DEPTH) == f.readline()[0],"The first line of the file must be the depth."
        while (line := f.readline()):
            assert line.startswith(URL_TEMPLATE % ''),"The urls do not start with the link."