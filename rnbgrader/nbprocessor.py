""" Check and process solution notebooks to generate exercise.

* Get code chunks
* Filter for presence of #- comments, indicating this is a question.
* Comments starting #<- should go into exercise without #<-; this allows stuff
  that would otherwise generate syntax errors etc.
* Check that each question has marks recorded with #m comment.
* Generate exercise, where:

  * code has been removed;
  * marks expanded to text of form "x marks / t (total T so far)"
"""

import re
import codecs
from argparse import ArgumentParser

from rnbgrader import loads
from rnbgrader.nbparser import Chunk, read_file

MARK_LINE_RE = re.compile(r'\s*#m\s+(([0-9]*[.])?[0-9]+)')

MARK_FULL_RE = re.compile(r"""^\s*\#-
                          \s+(\d+)
                          \s+marks
                          \s+/
                          \s+(\d+)
                          \s+\(total
                          \s+(\d+)""", re.VERBOSE)



def question_chunks(nb):
    return [chunk for chunk in nb.chunks
            if re.search('^\s*#-', chunk.code, re.M)]


def get_marks(code):
    for line in code.splitlines():
        match = MARK_RE.match(line)
        if match is not None:
            return tuple(float(v) for v in match.groups())
    return None, None, None


def check_marks(question_chunks, total):
    running = 0
    for chunk in question_chunks:
        mark, out_of, exp_running = get_marks(chunk.code)
        assert mark is not None
        assert out_of == total
        running += mark
        assert running == exp_running
    assert exp_running == total


def process_code(code, running=0, total=100):
    lines = []
    for line in code.splitlines(keepends=True):
        sline = line.strip()
        if not sline.startswith('#'):
            continue
        mark_match = MARK_LINE_RE.match(sline)
        if mark_match:
            mark = mark_match.groups()[0]
            lines.append('#- {} marks / {} (total {} so far)'.format(
                mark, total, running))
            running += mark
        elif sline.startswith('#<- '):
            lines.append(line.replace('#<- ', ''))
        elif sline.startswith('#-'):
            lines.append(line)
    return ''.join(lines), running


def replace_chunks(nb_str, chunks):
    lines = nb_str.splitlines(keepends=True)
    for chunk in chunks:
        lines[chunk.start_line] = chunk.code
        for line_no in range(chunk.start_line + 1, chunk.end_line + 1):
            lines[line_no] = ''
    return ''.join(lines)


def solution2exercise(nb, total):
    chunks = question_chunks(nb)
    chunks = [Chunk(process_code(c.code),
                    c.language,
                    c.start_line,
                    c.end_line)
              for c in chunks]
    return replace_chunks(nb.nb_str, chunks)


def make_check_exercise(solution_str, total):
    nb = loads(solution_str)
    exercise = solution2exercise(nb)
    check_marks(question_chunks(loads(exercise)), total)
    return exercise


def get_parser():
    parser = ArgumentParser(description="Marking for bio240")
    parser.add_argument('action',
                        help='one of "rebuild-solution", "grade"')
    parser.add_argument('notebook_file', default=None, nargs='?',
                        help='Notebook file to grade ("all" for all)')


def run_process():
    args = get_parser().parse_args()
    exercise = make_check_exercise(read_file(args.nb_fname))
    with codecs.open(args.out_fname, 'w', encoding='utf8') as fobj:
        fobj.write(exercise)
