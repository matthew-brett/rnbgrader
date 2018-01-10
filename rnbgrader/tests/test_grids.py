""" Test grading paths
"""

import numpy as np

from rnbgrader.chunkrunner import EvaluatedChunk
from rnbgrader.grids import full_grid, max_multi

from numpy.testing import assert_array_equal


def test_full_grid():
    # Test calculation of grid from results, answers. An answer returns marks
    # from a result.  Results are sequences of EvaluatedChunks. A evaluated
    # chunk is the association of (chunk, result). The grid contains NaN where
    # the result has not been compared to the answer, and a mark otherwise.  A
    # full grid compares all evaluated chunks to all answers.
    answers = [lambda x : 11 if x.results == [1] else 0,
               lambda x : 12 if x.results == [2] else 0,
               lambda x : 13 if x.results == [3] else 0,
               lambda x : 14 if x.results == [4] else 0]
    ev_chunks = [EvaluatedChunk(*t) for t in (
        (None, [1]), (None, [2]), (None, [3]), (None, [4]))]
    grid = full_grid(answers, ev_chunks)
    assert np.all(grid == np.diag([11, 12, 13, 14]))
    grid = full_grid(answers, ev_chunks[::-1])
    assert np.all(grid == np.fliplr(np.diag([11, 12, 13, 14])))
    grid = full_grid(answers[::-1], ev_chunks)
    assert np.all(grid == np.fliplr(np.diag([14, 13, 12, 11])))
    grid = full_grid(answers[::-1], ev_chunks[::-1])
    assert np.all(grid == np.diag([14, 13, 12, 11]))
    ev_chunks[2].results = None
    grid = full_grid(answers, ev_chunks)
    np.testing.assert_array_equal(grid, [[11, 0, 0, 0],
                                         [0, 12, 0, 0],
                                         [0, 0, 0, 0],
                                         [0, 0, 0, 14]])
    ev_chunks[2].results = [3]
    answers[2] = lambda x : 13 if x.results in ([3], [2]) else 0
    grid = full_grid(answers, ev_chunks)
    np.testing.assert_array_equal(grid, [[11, 0, 0, 0],
                                         [0, 12, 0, 0],
                                         [0, 13, 13, 0],
                                         [0, 0, 0, 14]])


def test_max_multi():
    assert_array_equal(max_multi([[1, 2], [3, 4]]), [2, 4])
    assert_array_equal(max_multi([[2, 1], [4, 3]]), [2, 4])
    # Same chunk gives max score on two questions.
    assert_array_equal(max_multi([[2, 1, 4], [4, 3, 6]]), [4, 6])
    # NaNs treated as zero
    assert_array_equal(max_multi([[2, np.nan, 4], [np.nan, 3, 6]]), [4, 6])
    assert_array_equal(max_multi([[np.nan, np.nan, np.nan], [np.nan, 3, 6]]),
                       [0, 6])
    assert_array_equal(max_multi(np.ones((4, 4))), np.ones((4,)))
    assert_array_equal(max_multi(np.ones((4, 4)) + np.nan), np.zeros((4,)))
