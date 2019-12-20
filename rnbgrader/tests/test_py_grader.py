""" Test grader module on Python
"""

from os.path import join as pjoin, dirname

import jupytext

from rnbgrader import JupyterKernel
from rnbgrader.grader import NBRunBase

DATA = pjoin(dirname(__file__), 'data')


def test_smoke():
    solution_rmd = pjoin(DATA, 'py_solution.Rmd')
    runner = NBRunBase()
    with JupyterKernel('python3', cwd=DATA) as pk:
        results0 = runner.run(solution_rmd, pk)
    contents = [c.results[0]['content'] if c.results else None
                for c in results0]
    assert contents[0] is None
    assert contents[1] == "['speed', 'dist']"
    assert contents[2] == '(50, 2)'
