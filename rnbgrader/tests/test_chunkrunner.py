""" Test nbrunner class
"""

from os.path import dirname, join as pjoin

from rnbgrader import ChunkRunner, load, loads

DATA_DIR = pjoin(dirname(__file__), 'data')
DEFAULT_NB = pjoin(DATA_DIR, 'default.Rmd')


def test_nbrunner():
    nb = load(DEFAULT_NB)
    runner = ChunkRunner(nb.chunks)
    assert len(nb.chunks) == 1
    assert len(runner.results) == 1
    assert len(runner.results[0]) == 2
    assert len(runner.results[0][1]) == 1
    assert runner.outcome == "ok"
    assert runner.message == None

    nb = loads("""\
```{r}
a = 1
b
```

```{r}
b = 2
b
```
""")
    runner = ChunkRunner(nb.chunks)
    assert len(nb.chunks) == 2
    assert len(runner.results) == 2
    assert runner.results[0][0] == nb.chunks[0]
    assert runner.results[0][1][0]['type'] == 'error'
    assert runner.results[1] == (nb.chunks[1], None)
    assert runner.outcome == "error"
    assert runner.message.startswith('Errors for chunk at line no 2:\n')
