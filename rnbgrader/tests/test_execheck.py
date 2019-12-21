""" Tests for execheck module
"""

import os.path as op

import numpy as np
import pandas as pd
import jupytext

from rnbgrader.execheck import (nb2kernel_name, nb2lang, exe_check_nb_fname,
                                do_exe_checks)
from rnbgrader.tmpdirs import in_dtemp


DATA = op.join(op.dirname(__file__), 'data')
RNB_FNAME = op.join(DATA, 'solution.Rmd')
PYNB_FNAME = op.join(DATA, 'py_solution.Rmd')


R_NOTEBOOK_STR = """\
Here is some text.

```{r}
# And a code cell
a <- 1
```
"""

PY_NOTEBOOK_STR = """\
Here is some text.

```{python}
# And a code cell
a = 1
```
"""


def test_nb_kernel():
    nb = jupytext.read(RNB_FNAME)
    assert nb2lang(nb) == 'R'
    # Requires ir kernel to be installed.
    assert nb2kernel_name(nb) == 'ir'
    nb = jupytext.reads(R_NOTEBOOK_STR, fmt='Rmd')
    assert nb2lang(nb) == 'R'
    assert nb2kernel_name(nb) == 'ir'
    nb = jupytext.read(PYNB_FNAME)
    assert nb2lang(nb) == 'python3'
    # Requires python3 kernel to be installed.
    assert nb2kernel_name(nb) == 'python3'
    # Default guess is R
    nb = jupytext.reads('', fmt='Rmd')
    assert nb2lang(nb) == 'R'
    # But can be overriden to Python
    nb = jupytext.reads(PY_NOTEBOOK_STR, fmt='Rmd')
    assert nb2lang(nb) == 'python'


R_NOTEBOOK_ERR_STR = """\
Here is some text.

```{r}
# And a code cell with an error
a <- b
```
"""

PY_NOTEBOOK_ERR_STR = """\
Here is some text.

```{python}
# And a code cell with an error
a = b
```
"""


def test_exe_check_nb_fname():
    assert exe_check_nb_fname(RNB_FNAME) == 'ok'
    assert exe_check_nb_fname(PYNB_FNAME) == 'ok'
    with in_dtemp():
        for nb_str in (R_NOTEBOOK_ERR_STR, PY_NOTEBOOK_ERR_STR):
            with open('nb.Rmd', 'wt') as fobj:
                fobj.write(nb_str)
            res = exe_check_nb_fname('nb.Rmd')
            assert '# And a code cell with an error' in res


def test_do_exe_checks():
    fnames = [RNB_FNAME, PYNB_FNAME]
    res = do_exe_checks(fnames)
    assert np.all(res == pd.Series({fn: 'ok' for fn in fnames}))
    res = do_exe_checks(fnames, fails_only=True)
    assert len(res) == 0
