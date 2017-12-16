""" Test notebook parser
"""

from os.path import dirname, join as pjoin
from glob import glob

from rnbgrader.nbparser import (read_file, load, loads, RMD_HEADER_RE,
                                _get_chunks, Chunk)


DATA_DIR = pjoin(dirname(__file__), 'data')
NB_DEFS = [dict(name='default',
                chunk_defs=(('r', 'plot(cars)\n'),)),
           dict(name='chunk_options',
                chunk_defs=(('r', 'a = 1\na\n'),
                            ('r', 'c = 5\nc\n'),
                            ('python', 'p = 10\np\n'),
                           )),
          ]
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
    for nb_def in NB_DEFS:
        fname = pjoin(DATA_DIR, nb_def['name'] + '.Rmd')
        nb = load(fname)
        assert (tuple((c.language, c.code) for c in nb.chunks) ==
                nb_def['chunk_defs'])


def test_rmd_header_re():
    assert (RMD_HEADER_RE.match('{r}') == None)
    assert (RMD_HEADER_RE.match('``` {r}') == None)
    assert (RMD_HEADER_RE.match('```{r}').groups() == ('r', ''))
    assert (RMD_HEADER_RE.match('```{r, echo=FALSE}').groups() ==
            ('r', 'echo=FALSE'))
    assert (RMD_HEADER_RE.match('```{r echo=FALSE}').groups() ==
            ('r', 'echo=FALSE'))
    assert (RMD_HEADER_RE.match('```{r  include=FALSE}').groups() ==
            ('r', 'include=FALSE'))
    assert (RMD_HEADER_RE.match('```{r  include=FALSE, echo =FALSE}').groups()
            == ('r', 'include=FALSE, echo =FALSE'))
    assert (RMD_HEADER_RE.match('```{r setup, include=FALSE}').groups() == 
            ('r', 'setup, include=FALSE'))


def get_chunks(nb_str):
    return [c.code for c in loads(nb_str).chunks]


def test__get_chunks():
    # Test the private function
    assert (_get_chunks('Foo\n\nBar\n```{r}\na = 1\nb =2\n```\nBaz') ==
            [Chunk('a = 1\nb =2\n', 'r')])


def test_get_chunks():
    assert get_chunks('') == []
    assert get_chunks('Foo\n\nBar\n') == []
    assert (get_chunks('Foo\n\nBar\n```{r}\na = 1\nb =2\n```\nBaz') ==
            ['a = 1\nb =2\n'])
    assert (get_chunks('Foo\n\nBar\n```{r}\na = 1\nb =2\n```\nBaz\n'
                      '```{r}\nc=2\n\nd=3\n\n```  \n\nSpam\n\nEggs\n') ==
            ['a = 1\nb =2\n', 'c=2\n\nd=3\n\n'])
    in_str = """\
```{r}
# One
```

```{r}
```
"""
    assert (get_chunks(in_str) == ['# One\n', ''])
