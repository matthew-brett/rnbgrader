""" R Markdown notebook parser

Parse notebook in R Markdown.

Extract code chunks from notebook.
"""

import re


def read_file(file_ish, encoding='utf8', errors='replace'):
    """ Read and return string contents in `file_ish`

    Parameters
    ----------
    file_ish : str or file-like
        String giving filename or file-like object implementing ``read``
        method.
    encoding : str
        Text encoding of file, default ``utf8``.
    errors : str
        Mode for encoding errors. See ``codec.Codec`` for a list.

    Returns
    -------
    contents : str
        Read, decoded contents of `file_ish`.
    """
    if hasattr(file_ish, 'read'):
        return file_ish.read()
    with open(file_ish, 'rt', encoding=encoding, errors=errors) as fobj:
        return fobj.read()


class Chunk(object):

    def __init__(self, code, language,
                 start_line,
                 end_line=None,
                 classes=(),
                 options='',
                 id='',
                 kvs=None):
        self.code = code
        self.language = language
        # line numbers are 0-based.
        self.start_line = start_line
        self.end_line = (start_line + len(code.splitlines()) - 1
                         if end_line is None else end_line)
        self.classes = tuple(classes)
        self.options = options
        self.id = id
        self.kvs = {} if kvs is None else kvs

    def __eq__(self, other):
        return self.__dict__ == other.__dict__


RMD_HEADER_RE = re.compile(r'^(\s*)```\s*{(\w+)(?:[, ]*)(.*?)}\s*$')


def _parse_chunks(nb_str):
    state = 'markdown'
    chunks = []
    for line_no, line in enumerate(nb_str.splitlines(keepends=True)):
        if state == 'markdown':
            match = RMD_HEADER_RE.match(line)
            if match is not None:
                indent, language, options = match.groups()
                start_line = line_no + 1
                state = 'chunk'
                code = []
            continue
        elif state == 'chunk':
            if line.rstrip() != indent + '```':
                if line.startswith(indent):
                    line = line[len(indent):]
                code.append(line)
                continue
            chunks.append(Chunk(''.join(code),
                                language,
                                start_line,
                                line_no -1))
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
        self._chunks = tuple(self._parse_chunks())

    def _parse_chunks(self):
        return _parse_chunks(self.nb_str)

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
