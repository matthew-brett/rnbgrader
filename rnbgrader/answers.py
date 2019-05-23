""" Answer classes and utility functions
"""

import re

import numpy as np

from PIL import Image


class Answer:

    def __init__(self, mark, tester, *, name=None):
        self.mark = mark
        self.tester = tester
        self.name = name

    def __call__(self, ev_chunk):
        if ev_chunk.results is None:
            return np.nan
        return self._grade(ev_chunk)

    def _grade(self, ev_chunk):
        return self.tester(ev_chunk)


class AnyAnswer(Answer):

    def _grade(self, ev_chunk):
        for result in ev_chunk.results:
            mark = self.tester(result)
            if mark > 0:
                return mark
        return 0


class TextAnswer(AnyAnswer):

    def __init__(self, mark, target, strip=False, *, name=None):
        self.mark = mark
        self.target = target.strip() if strip else target
        self.strip = strip
        self.name = name

    def _test(self, source):
        if self.strip:
            source = source.strip()
        return source == self.target

    def tester(self, result):
        if result['type'] not in ('text', 'stdout'):
            return 0
        return self.mark if self._test(result['content']) else 0


class StartTextAnswer(TextAnswer):

    def _test(self, source):
        return source.startswith(self.target)


class StrippedTextAnswer(TextAnswer):

    def __init__(self, mark, target, *, name=None):
        self.mark = mark
        self.lines = [L.strip() for L in target.splitlines()]
        self.name = name

    def _test(self, source):
        source_lines = [L.strip() for L in source.splitlines()]
        if len(source_lines) != len(self.lines):
            return False
        for s_line, t_line in zip(source_lines, self.lines):
            if s_line != t_line:
                return False
        return True


class RegexAnswer(TextAnswer):

    def __init__(self, mark, target, flags=0, *, name=None):
        self.mark = mark
        kwargs = {'flags': flags} if flags else {}
        self.regex = re.compile(target, **kwargs)
        self.name = name

    def _test(self, source):
        return self.regex.search(source)


_char_map = {40: '\\(',
             41: '\\)',
             91: '\\[',
             93: '\\]',
             123: '\\{',
             125: '\\}',
             63: '\\?',
             42: '\\*',
             43: '\\+',
             45: '\\-',
             124: '\\|',
             94: '\\^',
             36: '\\$',
             92: '\\\\',
             46: '\\.',
             38: '\\&',
             126: '\\~',
             35: '\\#',
             11: '\\\x0b',
             12: '\\\x0c'}


def raw2regex(literal):
    out = literal.translate(_char_map)
    # Space at beginning of lines is optional
    out = re.sub(r'^\s+', r'', out, flags=re.M)
    out = re.sub('^', r'\\s*', out, flags=re.M)
    # Space at end of lines is optional
    out = re.sub(r'\s+$', r'', out, flags=re.M)
    out = re.sub('$', r'\\s*', out, flags=re.M)
    # Newlines, Windows and Unix
    out = re.sub('\n', r'(?:\\n|\\r\\n?)', out)
    # Make whitespace match general for type, amount.
    return re.sub(r'\s+', r'\\s+', out)


class RawRegexAnswer(RegexAnswer):

    def __init__(self, mark, target, flags=0, *, name=None):
        super().__init__(mark, raw2regex(target), flags, name=name)


class ImgAnswer(AnyAnswer):

    def __init__(self, mark, expected, crop_box=None, thresh=None, bw=False,
                *, name=None):
        self.mark = mark
        if isinstance(expected, str):
            expected = Image.open(expected)
        self.expected = expected
        self.crop_box = crop_box
        self._cropped_expected = expected.crop(crop_box)
        self.thresh = (self._rms(self._cropped_expected) / 100
                       if thresh is None else thresh)
        self.bw = bw
        self.name = name

    def _cmp_image(self, other):
        this = self._cropped_expected
        other = other.crop(self.crop_box)
        if not other.size == this.size:
            return False
        if self.bw:
            this = this.convert('1')
            other = other.convert('1')
        diff = np.array(this) - np.array(other)
        return self._rms(diff) < self.thresh

    def _rms(self, img):
        return np.sqrt(np.mean(np.asarray(img) ** 2))

    def tester(self, result):
        if result['type'] != 'image':
            return 0
        return self.mark if self._cmp_image(result['content']) else 0


class BestOf(Answer):

    def __init__(self, answers, *, name=None):
        self.answers = answers
        self.name = name

    def _grade(self, ev_chunk):
        return max([answer._grade(ev_chunk) for answer in self.answers])


def make_bestof_texts(mark, texts, strip=False, *, name=None):
    return BestOf(
        [TextAnswer(mark, text, strip) for text in texts],
        name=name)


def make_bestof_images(mark, images, box, *, name=None):
    return BestOf(
        [ImgAnswer(mark, img, box) for img in images],
        name=name)


def apply_box(in_fname, out_fname, box):
    """ Write image filename `in_fname` with cropping in `box`

    A helper function.
    """
    in_img = Image.open(in_fname)
    out_img = in_img.crop(box)
    out_img.save(out_fname)
