""" Test grader module
"""

from os.path import join as pjoin, dirname
from io import StringIO
import re
from hashlib import sha1
from glob import glob
from copy import deepcopy

import numpy as np

from rnbgrader import JupyterKernel
from rnbgrader.grader import (OPTIONAL_PROMPT, MARK_MARKUP_RE, NBRunner,
                              report, duplicates, Grader, CanvasGrader,
                              NotebookError, CachedBuiltNotebook)
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
    nb_fileobj0 = StringIO("""
Text

```{r}
first_var <- 1
```

More text

```{r}
first_var
```
""")
    nb_fileobj1 = StringIO("""
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


class Skip:
    """ Flag to indicate we should skip this answer in compiling answers
    """
    pass


class CarsGrader(CanvasGrader):

    solution_rmds = (pjoin(DATA, 'solution.Rmd'),)
    standard_box = (44, 81, 800, 770)
    total = 50

    # Solution chunk positions, used in make_answers.
    # This allows testing different chunk position specifications.
    # Here we use simple positions.  Use Skip class to indicate we should
    # skip this question in the specification.
    _positions = tuple(range(1, 8))

    def make_answers(self):
        solution_dir = self.solution_dirs[0]
        # Positions are class variable to allow for testing different position
        # specifications.
        ps = self._positions

        if ps[0] is not Skip:
            self._chk_answer(RegexAnswer(
                5,
                OPTIONAL_PROMPT + r'50  2'),
                ps[0])

        raw = """
            'data.frame':	50 obs. of  2 variables:
            $ speed: num  4 4 7 7 8 9 10 10 10 11 ...
            $ dist : num  2 10 4 22 16 10 18 26 34 17 ..."""

        if ps[1] is not Skip:
            self._chk_answer(RegexAnswer(5, raw2regex(raw)), ps[1])

        raw = """
            speed dist
            1 4      2
            2 4     10
            3 7      4
            4 7     22
            5 8     16
            6 9     10"""
        if ps[2] is not Skip:
            self._chk_answer(RegexAnswer(5, raw2regex(raw)), ps[2])

        if ps[3] is not Skip:
            self._chk_answer(ImgAnswer(10,
                pjoin(solution_dir, 'chunk-4_item-0.png'),
                self.standard_box), ps[3])

        raw = """
            4  7  8  9 10 11 12 13 14 15 16 17 18 19 20 22 23 24 25 
            2  2  1  1  3  2  4  4  4  3  2  3  4  3  5  1  1  4  1"""
        if ps[4] is not Skip:
            self._chk_answer(RawRegexAnswer(5, raw), ps[4])

        raw = """
        speed dist
        27    16   32
        28    16   40
        29    17   32
        30    17   40
        31    17   50
        32    18   42"""
        if ps[5] is not Skip:
            self._chk_answer(RegexAnswer(10, raw2regex(raw)), ps[5])

        if ps[6] is not Skip:
            self._chk_img_answer(10, ps[6])


CARS_GRADER = CarsGrader()


def test_solutions_with_offsets():
    soln_fname = pjoin(DATA, 'solution.Rmd')
    # Basic position specification.
    assert sum(CARS_GRADER.grade_notebook(soln_fname)) == 50

    class G2(CarsGrader):
        # Strings for integer positions are OK.
        _positions = [str(i) for i in range(1, 8)]

    assert sum(G2().grade_notebook(soln_fname)) == 50

    class G3(CarsGrader):
        # Offsets OK, as long as there is a base.
        _positions = [1] + ['+1'] * 6

    assert sum(G3().grade_notebook(soln_fname)) == 50

    class G4(CarsGrader):
        # There must be a base.
        _positions = ['+1'] * 7

    with pytest.raises(ValueError):
        G4().grade_notebook(soln_fname)

    class G5(CarsGrader):
        # Can mix positions and offsets.
        _positions = [1, '+1', 3, 4, '+1', 6, '+1']

    assert sum(G5().grade_notebook(soln_fname)) == 50

    class G6(CarsGrader):
        # Can have offsets > 1
        _positions = [1, Skip, '+2', Skip, 5, Skip, '+2']
        total = 25

    assert sum(G6().grade_notebook(soln_fname)) == 25


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
    nb = StringIO("""

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
    bare_nb = StringIO("""

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

    annotated_nb = StringIO("""

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


def test_cached_nb_file_like():
    # Test we can used file-likes for notebook caching
    nb_text = """
Text

```{r}
#- A question
first_var <- 99
```

More text

```{r}
first_var
```

```{r}
#- Actual answer
first_var
```
"""
    nb_fobj = StringIO(nb_text)
    cbn = CachedBuiltNotebook(nb_fobj, NBRunner())
    assert len(cbn.solution) == 3
    assert cbn.solution[-1].chunk.code == '#- Actual answer\nfirst_var\n'


    class MyG(Grader):

        solution_rmds = (nb_fobj,)


    g = MyG()
    solns = g.solutions
    assert len(solns) == 1
    assert len(solns[0]) == 3


def assert_seq_equal(s1, s2):
    assert tuple(s1) == tuple(s2)


def test_chunk_is_answer():
    runner = NBRunner()
    nb_text = """
Text

```{r}
#- A question
first_var <- 99
```

More text

```{r}
first_var
```

```{r}
#- Actual answer
first_var
```
"""
    nb_fobj = StringIO(nb_text)
    with JupyterKernel('ir') as rk:
        chunks = runner.run(nb_fobj, rk)
    g = Grader()
    assert_seq_equal(chunks, g.clear_not_answers(chunks))
    # Second chunk has results.
    assert len(chunks[1].results) == 1

    # First check case where not-answer present raises error
    nb_fobj.seek(0)

    class MyG(Grader):

        solution_rmds = (nb_fobj,)
        total = 5

        def make_answers(self):
            self._chk_answer(RegexAnswer(
                5,
                OPTIONAL_PROMPT + r'99'),
                2)

    g = MyG()
    # Doesn't clear any chunks.
    assert_seq_equal(chunks, g.clear_not_answers(chunks))
    assert len(chunks[1].results) == 1
    # Therefore errors for duplicate outputs
    with pytest.raises(NotebookError):
        g.grade_notebook(StringIO(nb_text))

    # Check case with answer removed.
    class MyG2(MyG):

        solution_rmds = (nb_fobj,)

        def chunk_is_answer(self, chunk):
            return chunk.chunk.code != 'first_var\n'

    g2 = MyG2()
    # Clears output for not-answer chunk.
    cleared = deepcopy(chunks[1])
    cleared.results = []
    assert_seq_equal([chunks[0], cleared, chunks[2]], g2.clear_not_answers(chunks))
    # Answers now not duplicated.
    assert np.all(np.array(g2.grade_notebook(StringIO(nb_text))) ==
                  [5, 0, 0])
