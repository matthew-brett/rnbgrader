""" Test notebook parser
"""

from os.path import dirname, join as pjoin

from rnbgrader.nbparser import read_file, load, loads, as_chunks


DATA_DIR = pjoin(dirname(__file__), 'data')
NB_DEFAULT = pjoin(DATA_DIR, 'default.Rmd')


def test_read_file():
    with open(NB_DEFAULT, 'rt', encoding='utf8') as fobj:
        nb_text = fobj.read()
    assert nb_text == read_file(NB_DEFAULT)
    with open(NB_DEFAULT, 'rt', encoding='utf8') as fobj:
        assert nb_text == read_file(fobj)


def test_load_loads():
    with open(NB_DEFAULT, 'rt', encoding='utf8') as fobj:
        nb_text = fobj.read()
    nb_direct = load(NB_DEFAULT)
    nb_via_str = loads(nb_text)
    assert nb_direct == nb_via_str


def test_as_chunks():
    nb = load(NB_DEFAULT)
    chunks = as_chunks(nb)
    assert len(chunks) == 1
