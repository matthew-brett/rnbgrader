""" Grade notebook chunks against answers
"""

import numpy as np

from .kernels import JupyterKernel
from .chunkrunner import ChunkRunner


def answer_grid(answers, results):
    n_answers = len(answers)
    n_chunks = len(results)
    grid = np.zeros((n_answers, n_chunks))
    for a_no, answer in enumerate(answers):
        for c_no, (chunk, result) in enumerate(results):
            grid[a_no, c_no] = answer(result)
    return grid


def short_path(answers, results):
    grid = answer_grid(answers, results)





def grade(chunks, answers, kernel='ir', path_strategy=short_path):
    results = ChunkRunner(chunks, kernel).results
    # Path is sequence of (answer, result) tuples.
    path = path_strategy(answers, results)
    return sum(answer.mark for answer, result in path if result is not None)
