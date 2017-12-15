""" Test notebook parser
"""

from os.path import dirname, join as pjoin
from glob import glob

from rnbgrader.nbparser import read_file, load, loads, RMD_HEADER_RE


DATA_DIR = pjoin(dirname(__file__), 'data')
NB_DEFAULT = pjoin(DATA_DIR, 'default.Rmd')
ALL_NBS = glob(pjoin(DATA_DIR, '*.Rmd'))


def test_read_file():
    with open(NB_DEFAULT, 'rt', encoding='utf8') as fobj:
        nb_text = fobj.read()
    assert nb_text == read_file(NB_DEFAULT)
    with open(NB_DEFAULT, 'rt', encoding='utf8') as fobj:
        assert nb_text == read_file(fobj)


def test_load_loads():
    for nb_fname in ALL_NBS:
        with open(nb_fname, 'rt', encoding='utf8') as fobj:
            nb_text = fobj.read()
        nb_direct = load(nb_fname)
        nb_via_str = loads(nb_text)
        assert nb_direct == nb_via_str


def test_chunks():
    nb = load(NB_DEFAULT)
    assert len(nb.chunks) == 1


def test_rmd_header_re():
    assert (RMD_HEADER_RE.match('{r}').groups() == ('r', '', ''))
    assert (RMD_HEADER_RE.match('{r, echo=FALSE}').groups() ==
            ('r', 'echo=FALSE', ''))
    assert (RMD_HEADER_RE.match('{r echo=FALSE}').groups() ==
            ('r', 'echo=FALSE', ''))
    assert (RMD_HEADER_RE.match('{r  include=FALSE}').groups() ==
            ('r', 'include=FALSE', ''))
    assert (RMD_HEADER_RE.match('{r  include=FALSE, echo =FALSE}').groups() ==
            ('r', 'include=FALSE, echo =FALSE', ''))
    assert (RMD_HEADER_RE.match('{r setup, include=FALSE}').groups() == 
            ('r', 'setup, include=FALSE', ''))
    assert (RMD_HEADER_RE.match('{r echo=FALSE} a = 1').groups() ==
            ('r', 'echo=FALSE', 'a = 1'))


def get_chunks(nb_str):
    return [c.code for c in loads(nb_str).chunks]


def test_get_chunks():
    assert get_chunks('') == []
    assert get_chunks('Foo\n\nBar\n') == []
    assert (get_chunks('Foo\n\nBar\n```{r}\na = 1\nb =2\n```\nBaz') ==
            ['a = 1\nb =2'])
    assert (get_chunks('Foo\n\nBar\n```{r}\na = 1\nb =2\n```\nBaz\n'
                      '```{r}\nc=2\n\nd=3\n\n```  \n\nSpam\n\nEggs\n') ==
            ['a = 1\nb =2', 'c=2\n\nd=3\n'])
    in_str = """\
```{r}
# One
```

```{r}
```
"""
    assert (get_chunks(in_str) == ['# One', ''])
