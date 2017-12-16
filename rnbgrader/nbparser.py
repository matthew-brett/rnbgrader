""" R Notebook parser

Parse R notebook in R Markdown.

Extract code chunks from notebook.
"""

import re


def read_file(file_ish, encoding='utf8'):
    """ Read and return string contents in `file_ish`
    """
    if hasattr(file_ish, 'read'):
        return file_ish.read()
    with open(file_ish, 'rt', encoding=encoding) as fobj:
        return fobj.read()


class Chunk(object):

    def __init__(self, code, language, classes=(), options='', id='', kvs=None):
        self.language = language
        self.code = code
        self.classes = tuple(classes)
        self.id = id
        self.kvs = {} if kvs is None else kvs

    def __eq__(self, other):
        return self.__dict__ == other.__dict__


RMD_HEADER_RE = re.compile(r'^\s*```{(\w+)(?:[, ]*)(.*?)}\s*$')


def _get_chunks(nb_str):
    state = 'markdown'
    chunks = []
    for line in nb_str.splitlines(keepends=True):
        if state == 'markdown':
            match = RMD_HEADER_RE.match(line)
            if match is not None:
                language, options = match.groups()
                state = 'chunk'
                code = []
            continue
        elif state == 'chunk':
            if line.strip() != '```':
                code.append(line)
                continue
            chunks.append(Chunk(''.join(code), language))
            state = 'markdown'
    return chunks


class RNotebook(object):
    """ Object wrapping R Markdown notebook

    Properties: nb_str; chunks
    """

    def __init__(self, nb_str):
        """ Initialize object from string `nb_str`
        """
        self.nb_str = nb_str
        self._chunks = tuple(self._get_chunks())

    def _get_chunks(self):
        return _get_chunks(self.nb_str)

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
