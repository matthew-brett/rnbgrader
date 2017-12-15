""" R Notebook parser

Parse R notebook in R Markdown.

Extract code chunks from notebook.
"""

import re
import json
from collections import OrderedDict
from distutils.version import LooseVersion

from pypandoc import convert_text, get_pandoc_version

# The specified minimum version from
# https://cran.r-project.org/web/packages/rmarkdown/index.html
# as of 15 Dec 2017.
MINIMUM_PANDOC_VERSION = '1.12.3'

if LooseVersion(get_pandoc_version()) < MINIMUM_PANDOC_VERSION:
    raise RuntimeError('Need pandoc >= {} but have {}'.format(
        MINIMUM_PANDOC_VERSION, get_pandoc_version()))


def read_file(file_ish, encoding='utf8'):
    """ Read and return string contents in `file_ish`
    """
    if hasattr(file_ish, 'read'):
        return file_ish.read()
    with open(file_ish, 'rt', encoding=encoding) as fobj:
        return fobj.read()


class Chunk(object):

    def __init__(self, code, language, classes, options='', id='', kvs=None):
        self.language = language
        self.code = code
        self.classes = classes
        self.id = id
        self.kvs = {} if kvs is None else kvs


RMD_HEADER_RE = re.compile(r'{(\w+)(?:[, ]*)(.*?)}(?: *)(.*)')


def parse_codeblock(contents):
    (id, classes, kvs), code = contents
    kvs = OrderedDict(kvs)
    options = language = ''
    if len(classes) > 1:
        # We don't know what to do about this case (e.g. "R, something"), but
        # it probably cannot be an R Markdown chunk.
        return None
    elif len(classes) == 1:
        # Should always be just {r} for a chunk, but just in case ...
        match = RMD_HEADER_RE.match(classes[0])
        if match is None:
            # Could be some other Markdown code block formatting.
            return None
        language, options, _ = match.groups()
        assert _ == ''
    else:
        # We're expecting the code text to start with the {r whatever}
        # parameters.
        match = RMD_HEADER_RE.match(code)
        if match is None:
            return None
        language, options, code = match.groups()
    return Chunk(code, language, classes, options, id, kvs)


def _get_chunks(blocks):
    for block in blocks:
        if isinstance(block, list):
            yield from _get_chunks(block)
        elif not isinstance(block, dict):
            continue
        elif block['t'] in ('Code', 'CodeBlock'):
            chunk = parse_codeblock(block['c'])
            if chunk is not None:
                yield chunk
        elif 'c' in block and isinstance(block['c'], list):
            yield from _get_chunks(block['c'])


class RNotebook(object):
    """ Object wrapping R Markdown notebook

    Properties: nb_str; ast; chunks
    """

    def __init__(self, nb_str):
        """ Initialize object from string `nb_str`
        """
        self.nb_str = nb_str
        self._ast = json.loads(
            convert_text(nb_str, 'json', format='markdown'))
        self._chunks = tuple(self._get_chunks())

    def _get_chunks(self):
        return _get_chunks(self._get_ast_content())

    def _get_ast_content(self):
        # At some point before Pandoc 1.19.2.1, ast was a two-element list with
        # first element 'unMeta', second having content.
        ast = self.ast
        if hasattr(ast, 'keys'):
            return ast['blocks']
        assert list(ast[0].keys()) == ['unMeta']
        return ast[1]

    @property
    def ast(self):
        return self._ast

    @property
    def chunks(self):
        return self._chunks

    @classmethod
    def from_string(cls, in_str):
        """ Initialize from string `nb_str`, return as Notebook object
        """
        return cls(in_str)

    @classmethod
    def from_file(cls, file_ish):
        """ Initialize from contents of `file_ish`, return as Notebook object
        """
        return cls.from_string(read_file(file_ish))

    def __eq__(self, other):
        if not hasattr(other, 'nb_str'):
            return False
        return self.nb_str == other.nb_str


load = RNotebook.from_file

loads = RNotebook.from_string
