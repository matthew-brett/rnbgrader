""" Test notebook parser
"""

from os.path import dirname, join as pjoin
from glob import glob

from rnbgrader.nbparser import (read_file, load, loads, RMD_HEADER_RE, Chunk)


DATA_DIR = pjoin(dirname(__file__), 'data')
NB_DEFS = [dict(name='default',
                chunk_defs=(('r', 'plot(cars)\n', 11),
                           )),
           dict(name='chunk_options',
                chunk_defs=(('r', 'a = 1\na\n', 3),
                            ('r', 'c = 5\nc\n', 12),
                            ('python', 'p = 10\np\n', 17),
                           )),
           dict(name='list_chunk',
                chunk_defs=(('r', 'a = 1\na\n', 6),
                            ('r', 'b = 2\nb\n', 15),
                            ('r', 'c = 3\n  c\n', 21),
                            ('r', 'c\n'
                             '  ```\nSo the block continues '
                             'through the next code chunk\n```{r}\na\n', 27)
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
        assert (tuple((c.language, c.code, c.line_no) for c in nb.chunks) ==
                nb_def['chunk_defs'])


def test_chunk():
    chunk = Chunk('a = 1', 'python', 10)
    assert chunk.code == 'a = 1'
    assert chunk.language == 'python'
    assert chunk.line_no == 10
    assert chunk.classes == ()
    assert chunk.options == ''
    assert chunk.id == ''
    assert chunk.kvs == {}
    chunk2 = Chunk('a = 1', 'python', 10, (), '', '', {})
    assert chunk == chunk2


def test_rmd_header_re():
    assert (RMD_HEADER_RE.match('{r}') == None)
    assert (RMD_HEADER_RE.match('``` {r}') == None)
    assert (RMD_HEADER_RE.match('```{r}').groups() == ('', 'r', ''))
    assert (RMD_HEADER_RE.match('   ```{r}').groups() == ('   ', 'r', ''))
    assert (RMD_HEADER_RE.match('```{r, echo=FALSE}').groups() ==
            ('', 'r', 'echo=FALSE'))
    assert (RMD_HEADER_RE.match('```{r echo=FALSE}').groups() ==
            ('', 'r', 'echo=FALSE'))
    assert (RMD_HEADER_RE.match('```{r  include=FALSE}').groups() ==
            ('', 'r', 'include=FALSE'))
    assert (RMD_HEADER_RE.match('```{r  include=FALSE, echo =FALSE}').groups()
            == ('', 'r', 'include=FALSE, echo =FALSE'))
    assert (RMD_HEADER_RE.match('```{r setup, include=FALSE}').groups() == 
            ('', 'r', 'setup, include=FALSE'))
    assert (RMD_HEADER_RE.match('    ```{r setup, include=FALSE}').groups() == 
            ('    ', 'r', 'setup, include=FALSE'))


def get_chunks(nb_str):
    # Private testing function returns code and nothing else
    return [c.code for c in loads(nb_str).chunks]


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
