""" Test grader module
"""

import sys
from os.path import join as pjoin, dirname
import io
import re
from hashlib import sha1
from glob import glob

from rnbgrader import JupyterKernel
from rnbgrader.grader import (OPTIONAL_PROMPT, NBRunner, report, duplicates,
                              CanvasGrader, assert_answers_only,
                              RegexAnswer, ImgAnswer, raw2regex,
                              RawRegexAnswer)

import pytest

from gradools.canvastools import CanvasError

DATA = pjoin(dirname(__file__), 'data')


def test_optional_prompt():
    assert re.search(OPTIONAL_PROMPT, '[1] ') is not None
    assert re.search(OPTIONAL_PROMPT, '[100] ') is not None
    assert re.search(OPTIONAL_PROMPT, ' [100] ') is not None
    assert re.search(OPTIONAL_PROMPT + 'here', '[100] here') is not None
    assert re.search(OPTIONAL_PROMPT + 'here', '[100] here') is not None


def test_report():
    runner = NBRunner('some_var')
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

        return self._answers


CARS_GRADER = CarsGrader()


def test_raw2regex():
    raw = r""" Min. 1st Qu.  Median    Mean 3rd Qu.    Max.    NA's 
        4.00   23.00   40.00   41.73   48.00  190.00     960 """
    assert re.search(raw2regex(raw), raw)


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
