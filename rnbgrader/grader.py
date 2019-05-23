""" Process Notebooks, including solution.
"""

from os import makedirs
from os.path import (exists, join as pjoin, splitext, abspath, isdir, basename)
import pickle
from argparse import ArgumentParser
from glob import glob
from collections import defaultdict
from hashlib import sha1
from tempfile import TemporaryDirectory

import pandas as pd

from rnbgrader import load as nb_load, JupyterKernel, ChunkRunner
from rnbgrader.grids import full_grid, max_multi
from rnbgrader.answers import ImgAnswer


OPTIONAL_PROMPT = r'^\s*(?:\[\d+\] )?'


class NotebookError(Exception):
    """ Error running notebook """


class NBRunner:

    chunk_cls = ChunkRunner

    def __init__(self, subtract_var_name):
        self.subtract_var_name = subtract_var_name

    def process_chunks(self, chunks):
        """ Process chunks

        Notes
        -----
        You can use this function to process chunks you don't want to run, or
        want to modify.  For example, you might want to swap out a chunk that
        downloads data from a URL, replacing with a local load.
        """
        return chunks

    def get_chunks(self, fname):
        nb = nb_load(fname)
        return self.process_chunks(nb.chunks)

    def run(self, fname, rk):
        chunks = self.get_chunks(fname)
        # Clear all variables from kernel workspace
        rk.clear()
        rk.run_code(self.subtract_var_name + ' <- 0')
        # Unset troubling View function
        rk.run_code('View <- function(df) {}')
        runner = self.chunk_cls(chunks, rk)
        results = runner.results
        if runner.outcome != 'ok':
            raise NotebookError(
                f'Error running {fname}:\n{report(results)}')
        return results


def report(results):
    lines = []
    for i, cr in enumerate(results):
        code_lines = [L for L in cr.chunk.code.splitlines()
                      if not L.strip().startswith('#')]
        line0 = code_lines[0] if code_lines else '(no code)'
        outcome = cr.results[0]['content'] if cr.results else 'None'
        lines.append(f'{i: 2d}: {line0} - {outcome}')
    return '\n'.join(lines)


class CachedBuiltNotebook:

    def __init__(self, notebook_fname, runner, cache_dir=None,
                 timeout=30):
        self.notebook_fname = abspath(notebook_fname)
        self.runner = runner
        if cache_dir is None:
            self._tmp = TemporaryDirectory()
            cache_dir = self._tmp.name
        self.out_dir = pjoin(abspath(cache_dir),
                             basename(self.notebook_fname) + '.built')
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
            solution = self.runner.run(self.notebook_fname, rk)
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
    run_cls = NBRunner
    subtract_var_name = 'mkt__'
    total = 100

    def __init__(self):
        self.runner = self.run_cls(self.subtract_var_name)
        self._solution_nbs = tuple(
            self.cacher(nb, self.runner) for nb in self.solution_rmds)
        self.rebuild()

    def rebuild(self):
        for snb in self._solution_nbs:
            snb.rebuild()

    def reset_answers(self):
        self._answers = []

    def add_answer(self, answer):
        self._answers.append(answer)

    @property
    def answers(self):
        return self._answers

    def _chk_answer(self, answer, sol_chunk_no, solution_no=0):
        assert_answers_only(answer, sol_chunk_no,
                            self.solutions[solution_no])
        self.add_answer(answer)

    def _get_img_answer(self, points, sol_chunk_no, solution_no=0, *, name=None):
        soln_dir = self.solution_dirs[solution_no]
        return ImgAnswer(
            points,
            pjoin(soln_dir, f'chunk-{sol_chunk_no}_item-0.png'),
            self.standard_box,
            name=name)

    def _chk_img_answer(self, points, sol_chunk_no, solution_no=0, *, name=None):
        self._chk_answer(
            self._get_img_answer(points, sol_chunk_no, solution_no, name=name),
            sol_chunk_no,
            solution_no)

    @property
    def solutions(self):
        return [snb.solution for snb in self._solution_nbs]

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

    def grade_notebook(self, fname, answers=None):
        answers = self.make_check_answers() if answers is None else answers
        with JupyterKernel('ir') as rk:
            ev_chunks = self.runner.run(fname, rk)
            result = rk.run_code(self.subtract_var_name)
            # Stuff put in by me with patching
            extra = float(result[0]['content'].split()[1])
        grid = full_grid(answers, ev_chunks)
        names = [a.name if a.name else 'unnamed' for a in answers]
        names.append('adjustments')
        return pd.Series(list(max_multi(grid)) + [extra], names)

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

    def check_submissions(self, submissions):
        return

    def get_submissions(self, submission_dir):
        submissions = []
        for submission in sorted(glob(pjoin(submission_dir, '*'))):
            if not splitext(submission)[1].lower().startswith('.rmd'):
                continue
            submissions.append(submission)
        self.check_submissions(submissions)
        return submissions

    def main(self, args=None):
        parser = self.get_parser()
        args = parser.parse_args(args)
        if args.action == 'rebuild-solutions':
            self.rebuild()
        elif args.action == 'grade':
            if isdir(args.notebook_file):
                self.grade_all_notebooks(args.notebook_file,
                                         show_answers=args.show_answers)
            else:
                marks = self.grade_notebook(args.notebook_file)
                if not args.show_answers:
                    print(sum(marks))
                else:
                    print(marks, sum(marks))
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
        if i == chunk_no:
            assert answer(ev_chunk) > 0
        else:
            assert answer(ev_chunk) == 0
