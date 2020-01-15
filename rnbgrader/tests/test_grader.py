""" Test grader module
"""

from os.path import join as pjoin, dirname
import io
import re
from hashlib import sha1
from glob import glob

from rnbgrader import JupyterKernel
from rnbgrader.grader import (OPTIONAL_PROMPT, MARK_MARKUP_RE, NBRunner,
                              report, duplicates, Grader, CanvasGrader,
                              NotebookError)
from rnbgrader.answers import RegexAnswer, ImgAnswer, raw2regex, RawRegexAnswer

import pytest

from gradools.canvastools import CanvasError

DATA = pjoin(dirname(__file__), 'data')
MB_NB_FN = 'brettmatthew_139741_6519327_some_name.Rmd'
VR2_NB_FN = 'rodriguezvalia_140801_6518299_notebook.rmd'


def test_optional_prompt():
    assert re.search(OPTIONAL_PROMPT, '[1] ') is not None
    assert re.search(OPTIONAL_PROMPT, '[100] ') is not None
    assert re.search(OPTIONAL_PROMPT, ' [100] ') is not None
    assert re.search(OPTIONAL_PROMPT + 'here', '[100] here') is not None
    assert re.search(OPTIONAL_PROMPT + 'here', '[100] here') is not None


def test_report():
    runner = NBRunner()
    nb_fileobj0 = io.StringIO("""
Text

```{r}
first_var <- 1
```

More text

```{r}
first_var
```
""")
    nb_fileobj1 = io.StringIO("""
Text

```{r}
```

More text

```{r}
first_var <- 2
```
""")
    with JupyterKernel('ir') as rk:
        results0 = runner.run(nb_fileobj0, rk)
        results1 = runner.run(nb_fileobj1, rk)
    assert (report(results0) ==
            ' 0: first_var <- 1 - None\n 1: first_var - [1] 1')
    assert (report(results1) ==
            ' 0: (no code) - None\n 1: first_var <- 2 - None')



def test_duplicates():
    fnames = glob(pjoin(DATA, 'test_submissions', '*.Rmd'))
    with open(fnames[0], 'rb') as fobj:
        hash = sha1(fobj.read()).hexdigest()
    hashes = duplicates(glob(pjoin(DATA, 'test_submissions', '*')))
    assert list(hashes) == [hash]
    assert sorted(hashes[hash]) == sorted(fnames)


def test_get_submissions():
    g = CanvasGrader()
    pth = pjoin(DATA, 'test_submissions2')
    fnames = sorted(glob(pjoin(pth, '*')))
    assert g.get_submissions(pth) == fnames


def test_get_submissions_same_id():
    g = CanvasGrader()
    with pytest.raises(CanvasError):
        g.get_submissions(pjoin(DATA, 'test_submissions'))


class CarsGrader(CanvasGrader):

    solution_rmds = (pjoin(DATA, 'solution.Rmd'),)
    standard_box = (44, 81, 800, 770)
    total = 50

    def make_answers(self):
        solution_dir = self.solution_dirs[0]

        self._chk_answer(RegexAnswer(
            5,
            OPTIONAL_PROMPT + r'50  2'),
            1)

        raw = """
            'data.frame':	50 obs. of  2 variables:
            $ speed: num  4 4 7 7 8 9 10 10 10 11 ...
            $ dist : num  2 10 4 22 16 10 18 26 34 17 ..."""
        self._chk_answer(RegexAnswer(5, raw2regex(raw)), 2)

        raw = """
            speed dist
            1 4      2  
            2 4     10  
            3 7      4  
            4 7     22  
            5 8     16  
            6 9     10"""
        self._chk_answer(RegexAnswer(5, raw2regex(raw)), 3)

        self._chk_answer(ImgAnswer(10,
            pjoin(solution_dir, 'chunk-4_item-0.png'),
            self.standard_box), 4)

        raw = """
            4  7  8  9 10 11 12 13 14 15 16 17 18 19 20 22 23 24 25 
            2  2  1  1  3  2  4  4  4  3  2  3  4  3  5  1  1  4  1"""
        self._chk_answer(RawRegexAnswer(5, raw), 5)

        raw = """
        speed dist
        27    16   32
        28    16   40
        29    17   32
        30    17   40
        31    17   50
        32    18   42"""
        self._chk_answer(RegexAnswer(10, raw2regex(raw)), 6)

        self._chk_img_answer(10, 7)


CARS_GRADER = CarsGrader()


def test_solution():
    assert sum(CARS_GRADER.grade_notebook(
        pjoin(DATA, 'solution.Rmd'))) == 50


def test_bit_bad():
    # This one has a couple of wrong answers
    assert sum(CARS_GRADER.grade_notebook(
        pjoin(DATA, 'not_solution.Rmd'))) == 35


def test_grade_all_error():
    with pytest.raises(CanvasError):
        CARS_GRADER.grade_all_notebooks(pjoin(DATA, 'test_submissions'))


def test_main():
    args = ["foo"]
    assert CARS_GRADER.main(args) == 1


def test_check_names():
    args = ["check-names", pjoin(DATA, "test_submissions")]
    with pytest.raises(CanvasError):
        CARS_GRADER.main(args)


def test_error_report():
    nb = io.StringIO("""

Some text.

```{r}
a <- 1
a
```

More text.

```{r}
b
```
""")
    runner = NBRunner()
    with pytest.raises(NotebookError):
        with JupyterKernel('ir') as rk:
            runner.run(nb, rk)


def test_mark_markup():
    assert MARK_MARKUP_RE.match('#M: -2.5').groups() == ('-2.5',)
    assert MARK_MARKUP_RE.match('#M:-2.5').groups() == ('-2.5',)
    assert MARK_MARKUP_RE.match('# M : -2.5').groups() == ('-2.5',)
    assert MARK_MARKUP_RE.search('foo\n# M : -2.5  \nbar').groups() == ('-2.5',)
    assert MARK_MARKUP_RE.search('foo  # M : -2.5  \nbar') is None
    assert MARK_MARKUP_RE.match('#M : -2.5  ').groups() == ('-2.5',)
    assert MARK_MARKUP_RE.match('#M : +2.5  ').groups() == ('+2.5',)
    assert MARK_MARKUP_RE.match('#M : +22. ').groups() == ('+22.',)
    assert MARK_MARKUP_RE.match('#M : 11.999 ').groups() == ('11.999',)
    assert MARK_MARKUP_RE.match('\t#M : -2.5  ').groups() == ('-2.5',)
    assert MARK_MARKUP_RE.match('#M: --2.5') is None
    assert MARK_MARKUP_RE.match('#M: +-2.5') is None
    assert MARK_MARKUP_RE.match('#M: ++2.5') is None
    assert MARK_MARKUP_RE.match('#M: 2.5 ish') is None


def test_initial_check():
    g = CanvasGrader()
    with pytest.raises(CanvasError):
        g.initial_check(pjoin(DATA, 'test_submissions'))
    with pytest.raises(NotebookError):
        g.initial_check(pjoin(DATA, 'test_submissions_markup'))
    pth = pjoin(DATA, 'test_submissions2')
    res = g.initial_check(pth)
    mb = pjoin(pth, MB_NB_FN)
    with open(mb, 'rb') as fobj:
        mb_sha = sha1(fobj.read()).hexdigest()
    assert res == {mb_sha: [mb, pjoin(pth, VR2_NB_FN)]}


def test_markup_in_nb():
    bare_nb = io.StringIO("""

Some text.

```{r}
a <- 1
a
```

More text.

#M: 10

```{r}
b <- 2
```
""")
    assert CARS_GRADER.mark_markups(bare_nb) == ()

    annotated_nb = io.StringIO("""

Some text.

```{r}
a <- 1
a
# M: 2.0
```

More text.

#M: 10

```{r}
#M : -2.5
b <- 2
```
""")

    assert CARS_GRADER.mark_markups(annotated_nb) == (2., -2.5)


def test_raise_for_markup():
    g = Grader()
    for sdir in ('test_submissions', 'test_submissions2'):
        pth = pjoin(DATA, sdir)
        g.raise_for_markup(g.get_submissions(pth))


def test_markup_used():
    g = CARS_GRADER
    pth = pjoin(DATA, 'test_submissions_markup')
    mb = pjoin(pth, MB_NB_FN)
    vr2 = pjoin(pth, VR2_NB_FN)
    assert g.mark_markups(mb) == (-2, 42)
    assert g.mark_markups(vr2) == ()
    mb_marks = g.grade_notebook(mb)
    assert list(mb_marks.index) == ['unnamed'] * 7 + ['adjustments', 'markups']
    assert sum(mb_marks) == 80
    assert sum(g.grade_notebook(vr2)) == 40
