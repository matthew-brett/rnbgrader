""" Calculate answer, evaluated chunk score grids

A grid is a 2D array, with rows corresponding to answer, and columns
corresponding to evalulated chunks.

The array contains marks, where the evaluated chunk gets the corresponding
marks from the given answer.

An answer returns marks from an evaluated chunk.  A evaluated chunk is the
association of (chunk, result).
"""

import numpy as np


def full_grid(answers, evaluated_chunks):
    """ Calculate full grid of `answers` against `evaluated_chunks`.

    A grid is a 2D array, with rows corresponding to answer, and columns
    corresponding to evaluated chunks.

    The array contains marks, where the evaluated chunk gets the corresponding
    marks from the given answer.

    Parameters
    ----------
    answers : length N sequence of callables.
        Sequence of callable objects, returning marks for given evaluated chunk
        (see below).
    evaluated_chunks : length P sequence of evaluated chunks
        Sequence of EvaluatedChunk instances.

    Returns
    -------
    grid : ndarray shape (N, P)
        Array where rows correspond to answers and columns to evaluated chunks.
        The value at ``grid[i, j]`` is the mark for result[j] on question[i]`.
    """
    N = len(answers)
    P = len(evaluated_chunks)
    grid = np.zeros((N, P))
    for i, answer in enumerate(answers):
        for j, ev_chunk in enumerate(evaluated_chunks):
            grid[i, j] = answer(ev_chunk)
    return grid


def max_multi(grid):
    """ Allow any evaluated chunk as answer to any question

    Treat NaN values as zero.

    Parameters
    ----------
    grid : ndarray shape (N, P)
        Array where rows correspond to answers and columns to evaluated chunks.
        The value at ``grid[i, j]`` is the mark for result[j] on question[i]`.

    Returns
    -------
    scores : array shape(N,) of float
        Scores, that are scores for the chunks giving maximum score for each
        answer.
    """
    # Treat NaNs as zeros.  Nansum will also do this for numpy >= 1.9
    grid = np.array(grid)
    grid[np.isnan(grid)] = 0
    return np.max(grid, axis=1)
