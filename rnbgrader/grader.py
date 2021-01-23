""" Process Notebooks, including solution.
"""

from os import makedirs
from os.path import (exists, join as pjoin, splitext, abspath, isdir, basename)
from io import StringIO
import pickle
from argparse import ArgumentParser
from glob import glob
from collections import defaultdict
from hashlib import sha1
from tempfile import TemporaryDirectory
import re

import pandas as pd

from rnbgrader import load as nb_load, JupyterKernel, ChunkRunner
from rnbgrader.grids import full_grid, max_multi
from rnbgrader.answers import ImgAnswer


OPTIONAL_PROMPT = r'^\s*(?:\[\d+\] )?'

MARK_MARKUP_RE = re.compile(r'^\s*#\s*M\s*:\s*([-+]?[.0-9]+)\s*$', re.M)


class NotebookError(Exception):
    """ Error running notebook """


class NBRunner:

    chunk_cls = ChunkRunner

    def process_chunks(self, chunks):
        """ Process chunks

        Notes
        -----
        You can use this function to process chunks you don't want to run, or
        want to modify.  For example, you might want to swap out a chunk that
        downloads data from a URL, replacing with a local load.
        """
        return chunks

    def get_chunks(self, fileish):
        nb = nb_load(fileish)
        return self.process_chunks(nb.chunks)

    def pre_run(self, rk):
        """ Run pre-loading etc code.

        Notes
        -----
        You can use this function to run code to initialize the notebook.
        Examples might be setting variables used in marking, or redefining
        functions to restrict complexity or disable them.
        """
        pass

    def post_run(self, rk):
        """ Run code at end of notebook.

        Notes
        -----
        You can use this function to run code at the end of the notebook.
        An example might be deleting temporary files.
        """
        pass

    def run(self, fileish, rk):
        chunks = self.get_chunks(fileish)
        self.pre_run(rk)
        runner = self.chunk_cls(chunks, rk)
        results = runner.results
        if runner.outcome != 'ok':
            raise NotebookError(
                f'Error running {get_fname(fileish)}:\n{report(results)}')
        self.post_run(rk)
        return results


def get_fname(fileish):
    """ Return filename from `fileish`
    """
    if isinstance(fileish, str):
        return fileish
    return getattr(fileish, 'name', "<file object>")


def report(results):
    lines = []
    for i, cr in enumerate(results):
        code_lines = [L for L in cr.chunk.code.splitlines()
                      if not L.strip().startswith('#')]
        line0 = code_lines[0] if code_lines else '(no code)'
        outcome = cr.results[0]['content'] if cr.results else 'None'
        lines.append(f'{i: 2d}: {line0} - {outcome}')
    return '\n'.join(lines)


def _read_reset(fobj):
    """ Read file-like `fobj` from current position, reset position

    Parameters
    ----------
    fobj : file-like object
        Implements ``tell``, ``seek`` and ``read``.

    Returns
    -------
    contents : str
        Contents read from file-like from starting position, as given by
        ``fobj.tell()`` on entry to the function.  Position reset to starting
        position after read.
    """
    pos = fobj.tell()
    contents = fobj.read()
    fobj.seek(pos)
    return contents


class CachedBuiltNotebook:

    def __init__(self, notebook_fileish, runner, cache_dir=None,
                 timeout=30):
        """ Initialize cached, built notebook object

        Parameters
        ----------
        notebook_fileish : file-like
            Filename or file-like object implementing ``read``.
        runner : :class:`NBRunner` instance
            Implements `run` method.
        cache_dir : {None, str}, optional
            Path to store cached results.  None results in a temporary
            directory.
        timeout : int, optional
            Timeout for running individual cells.
        """
        if hasattr(notebook_fileish, 'read'):  # file object.
            self.notebook_text = _read_reset(notebook_fileish)
            self._nb_froot = sha1(
                self.notebook_text.encode('latin1')).hexdigest()
        else:  # Filename.
            with open(notebook_fileish, 'rt') as fobj:
                self.notebook_text = fobj.read()
            self._nb_froot = basename(notebook_fileish)
        self.runner = runner
        if cache_dir is None:
            self._tmp = TemporaryDirectory()
            cache_dir = self._tmp.name
        self.out_dir = pjoin(abspath(cache_dir), self._nb_froot + '.built')
        self.timeout = timeout
        self.pkl_fname = pjoin(self.out_dir, 'solution.pkl')
        self._solution = None

    @property
    def solution(self):
        if self._solution is None:
            self._solution = self._get_solution()
        return self._solution

    def _get_solution(self):
        if not exists(self.pkl_fname):
            return self.rebuild()
        with open(self.pkl_fname, 'rb') as fobj:
            return pickle.load(fobj)

    def rebuild(self):
        # Rebuild solution notebooks
        if not isdir(self.out_dir):
            makedirs(self.out_dir)
        with JupyterKernel('ir', timeout=self.timeout) as rk:
            solution = self.runner.run(StringIO(self.notebook_text), rk)
        self._store_solution(solution)
        return solution

    def _store_solution(self, solution):
        with open(self.pkl_fname, 'wb') as fobj:
            pickle.dump(solution, fobj)
        store_images(solution, self.out_dir)


def print_solution(solution):
    for i, s in enumerate(solution):
        content = s.results[0]['content'] if s.results else '[None]'
        print(f'{i}\n{s.chunk.code}\n{content}\n')


class Grader:

    solution_rmds = ()
    standard_box = (44, 81, 800, 770)
    cacher = CachedBuiltNotebook
    run_maker = NBRunner
    total = 100

    def __init__(self):
        self.runner = self.run_maker()
        self._solution_nbs = tuple(
            self.cacher(nb, self.runner) for nb in self.solution_rmds)
        self.rebuild()

    def rebuild(self):
        for snb in self._solution_nbs:
            snb.rebuild()

    def reset_answers(self):
        self._answers = []
        self._last_soln_chunk_no = None

    def add_answer(self, answer, soln_chunk_no=None):
        self._answers.append(answer)
        self._last_soln_chunk_no = soln_chunk_no

    @property
    def answers(self):
        return self._answers

    def _lookup_chunk(self, chunk_no):
        if isinstance(chunk_no, str):
            if chunk_no[0] in ('-+'):
                # Relative offset without origin.
                if self._last_soln_chunk_no is None:
                    raise ValueError('String chunk no with unset last chunk '
                                     'no attribute')
                return self._last_soln_chunk_no + int(chunk_no)
        return int(chunk_no)

    def _chk_answer(self, answer, soln_chunk_spec, solution_no=0):
        soln_chunk_no = self._lookup_chunk(soln_chunk_spec)
        assert_answers_only(answer, soln_chunk_no,
                            self.solutions[solution_no])
        self.add_answer(answer, soln_chunk_no)

    def _get_img_answer(self, points, soln_chunk_no, solution_no=0, *,
                        name=None):
        soln_dir = self.solution_dirs[solution_no]
        return ImgAnswer(
            points,
            pjoin(soln_dir, f'chunk-{soln_chunk_no}_item-0.png'),
            self.standard_box,
            name=name)

    def _chk_img_answer(self, points, soln_chunk_spec, solution_no=0, *,
                        name=None):
        soln_chunk_no = self._lookup_chunk(soln_chunk_spec)
        self._chk_answer(
            self._get_img_answer(points, soln_chunk_no, solution_no,
                                 name=name),
            soln_chunk_no,
            solution_no)

    @property
    def solutions(self):
        solutions = []
        for snb in self._solution_nbs:
            solutions.append(self.clear_not_answers(snb.solution))
        return solutions

    @property
    def solution_dirs(self):
        return [snb.out_dir for snb in self._solution_nbs]

    def make_answers(self):
        # Optionally, return answers
        return []

    def check_answers(self, answers):
        """ Crude score algorithm gives correct total for first solution
        """
        grid = full_grid(answers, self.solutions[0])
        assert sum(max_multi(grid)) == self.total

    def make_check_answers(self):
        self.reset_answers()
        res = self.make_answers()
        answers = self._answers if res is None else res
        self.check_answers(answers)
        return answers

    def get_parser(self):
        parser = ArgumentParser(description="R notebook marking")
        parser.add_argument('action',
                            help='one of "rebuild-solutions", "grade"')
        parser.add_argument('notebook_file', default=None, nargs='?',
                            help='Notebook file to grade (can be directory)')
        parser.add_argument('--show-answers', action='store_true',
                            help="Show scores for individual answers")
        return parser

    def chunk_is_answer(self, chunk):
        # Override to remove chunks that should not be taken as answers.
        return True

    def clear_not_answers(self, ev_chunks):
        """ Clear results for chunks identified as not-answers
        """
        out_chunks = []
        for c in ev_chunks:
            if not self.chunk_is_answer(c):
                c.results = []
            out_chunks.append(c)
        return tuple(out_chunks)

    def calc_adjustments(self, rk):
        """ Calculate adjustments at end of notebook, using kernel.
        """
        return 0

    def grade_notebook(self, fileish, answers=None):
        answers = self.make_check_answers() if answers is None else answers
        with JupyterKernel('ir') as rk:
            ev_chunks = self.runner.run(fileish, rk)
            adjustments = self.calc_adjustments(rk)
        # Remove any not-answer chunks
        ev_chunks = self.clear_not_answers(ev_chunks)
        # Get adjustments from markup
        markups = sum(self.mark_markups(fileish))
        grid = full_grid(answers, ev_chunks)
        names = [a.name if a.name else 'unnamed' for a in answers]
        names += ['adjustments', 'markups']
        return pd.Series(list(max_multi(grid)) + [adjustments, markups], names)

    def grade_all_notebooks(self, submission_dir, show_answers=False):
        answers = self.make_check_answers()
        for submission in self.get_submissions(submission_dir):
            try:
                marks = self.grade_notebook(abspath(submission), answers)
            except NotebookError as nbe:
                print(str(nbe))
                continue
            if not show_answers:
                print(submission, sum(marks))
                continue
            print(submission, marks, sum(marks))

    def print_solution(self, solution_no=0):
        for i, s in enumerate(self.solutions[solution_no]):
            content = s.results[0]['content'] if s.results else '[None]'
            print(f'{i}\n{s.chunk.code}\n{content}\n')

    def print_solutions(self):
        for i in range(len(self.solution_rmds)):
            print(f'Notebook: {self.solution_rmds[i]}\n')
            self.print_solution(i)
            print('\n')

    def mark_markups(self, fileish):
        """ Return marks from mark markup lines
        """
        nb = nb_load(fileish)
        markups = []
        for chunk in nb.chunks:
            markups += MARK_MARKUP_RE.findall(chunk.code)
        return tuple(float(m) for m in markups)

    def raise_for_markup(self, submissions):
        """ Check submissions for markup

        There should be no markup when first submitted.
        """
        for submission in submissions:
            if self.mark_markups(submission) != ():
                raise NotebookError(f'{submission} contains markup')

    def initial_check(self, submission_dir):
        """ Run check of initial submissions
        """
        submissions = self.get_submissions(submission_dir)
        self.raise_for_markup(submissions)
        return duplicates(submissions)

    def check_submissions(self, submissions):
        """ Inherit and override to add checking for valid filenames etc
        """
        return

    def get_submissions(self, submission_dir):
        """ Return filenames of submissions """
        submissions = []
        for submission in sorted(glob(pjoin(submission_dir, '*'))):
            if not splitext(submission)[1].lower().startswith('.rmd'):
                continue
            submissions.append(submission)
        self.check_submissions(submissions)
        return submissions

    def do_grade(self, notebook_spec, show_answers):
        if isdir(notebook_spec):
            self.grade_all_notebooks(notebook_spec,
                                     show_answers=show_answers)
            return
        marks = self.grade_notebook(notebook_spec)
        if not show_answers:
            print(sum(marks))
        else:
            print(marks, sum(marks))

    def main(self, args=None):
        parser = self.get_parser()
        args = parser.parse_args(args)
        if args.action == 'rebuild-solutions':
            self.rebuild()
        elif args.action == 'grade':
            self.do_grade(args.notebook_file, args.show_answers)
        elif args.action == 'check-names':
            list(self.get_submissions(args.notebook_file))
            return 0
        elif args.action == 'print-solutions':
            self.print_solutions()
            return 0
        else:
            print('action should be one of "rebuild-solution", "grade", '
                  '"check-names", "print-solutions"')
            return 1
        return 0


class CanvasGrader(Grader):

    def check_submissions(self, submissions):
        from gradools.canvastools import check_unique_stid
        check_unique_stid(submissions)


def store_images(solution, out_dir):
    # Assumes `out_dir` exists
    for i, ev_chunk in enumerate(solution):
        for j, result in enumerate(ev_chunk.results):
            if result['type'] != 'image':
                continue
            out_fname = pjoin(out_dir, 'chunk-{}_item-{}.png'.format(i, j))
            result['content'].save(out_fname)


def duplicates(filenames):
    hashes = defaultdict(list)
    for fname in filenames:
        with open(fname, 'rb') as fobj:
            hash = sha1(fobj.read()).hexdigest()
            hashes[hash].append(fname)
    return {hash: entries for hash, entries in hashes.items()
              if len(entries) > 1}


def assert_answers_only(answer, chunk_no, solution):
    """ Check that answer `answer` only corresponds to ``solution[chunk_no]``
    """
    for i, ev_chunk in enumerate(solution):
        code = ev_chunk.chunk.code
        a_name = '"unnamed"' if answer.name is None else answer.name
        if i == chunk_no:
            if answer(ev_chunk) == 0:
                raise NotebookError(
                    f'{i}: {code} does not give marks for {a_name}')
            continue
        if answer(ev_chunk) != 0:
            raise NotebookError(
                f'{i}: {code} gives marks for {a_name}, '
                f'but this should only be true for chunk {chunk_no}')

