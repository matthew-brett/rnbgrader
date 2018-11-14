""" Tests for nbprocessor module
"""

from os.path import dirname, join as pjoin
import codecs
from rnbgrader import load, loads
from rnbgrader.nbprocessor import (make_check_exercise, solution2exercise,
                                   check_marks, question_chunks, process_code)


HERE = dirname(__file__)
SOLUTION_FNAME = pjoin(HERE, 'solution.Rmd')
EXERCISE_FNAME = pjoin(HERE, 'exercise.Rmd')
with codecs.open(SOLUTION_FNAME, 'r', encoding='utf8') as _fobj:
    SOLUTION_STR = _fobj.read()
with codecs.open(EXERCISE_FNAME, 'r', encoding='utf8') as _fobj:
    EXERCISE_STR = _fobj.read()


def test_make_check_exercise():
    assert make_check_exercise(SOLUTION_STR) == EXERCISE_STR


def test_solution2exercise():
    nb = load(SOLUTION_FNAME)
    exercise = solution2exercise(nb)
    check_marks(question_chunks(loads(exercise)))


def test_check_marks():
    nb = load(SOLUTION_FNAME)
    q_chunks = question_chunks(nb)
    check_marks(q_chunks)


def test_process_code():
    assert process_code('#- foo\n#- bar') == '#- foo\n#- bar'
    assert process_code('#- foo\na = 1\n#- bar') == '#- foo\n#- bar'
    assert process_code('#- foo\na = 1\n# bar') == '#- foo\n'
    assert process_code('#- foo\n#<- a = ?\n# bar') == '#- foo\na = ?\n'
    assert process_code('#- foo\n#<- a = ?\n#- bar') == '#- foo\na = ?\n#- bar'
    assert (process_code('#- foo\n  #<- a = ?\n#- bar') ==
            '#- foo\n  a = ?\n#- bar')
